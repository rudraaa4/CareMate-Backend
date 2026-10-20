# Deploying CareMate on AWS

A small, low-cost reference deployment: one API container on EC2, a private
PostgreSQL database on RDS, documents in a private S3 bucket, secrets in SSM
Parameter Store. It is a demonstration of the architecture, not a hardened
production setup (see "What production would add").

```
Internet
   |  :8000 (your IP only)
   v
[ EC2 t3.micro  - public subnet ]  --IAM role-->  [ S3 bucket (private, encrypted) ]
   |  Docker: CareMate API         --IAM role-->  [ SSM Parameter Store: SECRET_KEY, DB password ]
   |  :5432 (only from the EC2 security group)
   v
[ RDS PostgreSQL - private subnets, not publicly accessible ]
```

## Network

- One VPC, two availability zones, one public and one private subnet in each.
  **No NAT gateway** (it is billed hourly and nothing here needs one).
- Add the free S3 gateway endpoint so S3 traffic stays inside AWS.
- Security groups:
  - `caremate-app-sg`: inbound TCP 8000 from your IP, TCP 22 from your IP.
  - `caremate-db-sg`: inbound TCP 5432 from `caremate-app-sg` only.

## Data and secrets

- **RDS**: PostgreSQL, Free tier template, single-AZ, smallest instance,
  20 GB, *Public access: No*, initial database name `caremate`,
  master user `caremate_user`, an alphanumeric password.
- **S3**: one bucket, *Block all public access* on, default encryption on.
- **SSM Parameter Store** (type `SecureString`):
  - `/caremate/SECRET_KEY`: output of
    `python -c "import secrets; print(secrets.token_hex(32))"`
  - `/caremate/DB_PASSWORD`: the RDS master password

## IAM role for the EC2 instance

Trust: EC2. Inline policy (replace the bucket name and region/account):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET/*"
    },
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter"],
      "Resource": "arn:aws:ssm:REGION:ACCOUNT_ID:parameter/caremate/*"
    }
  ]
}
```

The application never sees an access key: boto3 picks up the role's
temporary credentials automatically.

## Run it on the instance (Amazon Linux 2023)

```bash
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user      # log out and back in afterwards

git clone -b aws-deploy https://github.com/rudraaa4/CareMate-Backend.git
cd CareMate-Backend/backend
docker build -t caremate .
```

Create the environment file from Parameter Store (nothing secret is stored
in git or in the image):

```bash
REGION=ap-south-1                       # your region
SECRET_KEY=$(aws ssm get-parameter --region $REGION --name /caremate/SECRET_KEY --with-decryption --query Parameter.Value --output text)
DB_PASSWORD=$(aws ssm get-parameter --region $REGION --name /caremate/DB_PASSWORD --with-decryption --query Parameter.Value --output text)

cat > ~/caremate.env <<EOF
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://caremate_user:${DB_PASSWORD}@YOUR-RDS-ENDPOINT:5432/caremate
SECRET_KEY=${SECRET_KEY}
STORAGE_BACKEND=s3
S3_BUCKET=YOUR-BUCKET
AWS_REGION=${REGION}
EOF
chmod 600 ~/caremate.env
```

Start the API (host networking lets the container reach the instance's
IAM credentials without extra metadata-hop configuration):

```bash
docker run -d --name caremate --restart unless-stopped \
  --network host --env-file ~/caremate.env caremate
docker logs -f caremate        # migrations run first, then Uvicorn starts
```

Open `http://<ec2-public-ip>:8000/docs`.

## Verify

1. `GET /api/health` returns `{"status": "UP", ..., "database": "UP"}`.
2. Register, log in (Authorize), add a medicine.
3. Upload a PDF via `POST /api/v1/documents`; the object appears in the S3
   bucket (console, or `aws s3 ls s3://YOUR-BUCKET`), and downloads work
   through `GET /api/v1/documents/{id}/download` only.

## Tear down (avoid charges)

Delete in this order: EC2 instance, RDS instance (skip the final snapshot),
S3 bucket (empty it first), SSM parameters, security groups, VPC. Check the
Billing page the next day.

## What production would add

HTTPS behind an Application Load Balancer (ACM certificate), an Auto Scaling
group for the API, Multi-AZ RDS with automated backups, a NAT gateway or
VPC endpoints for private compute, CloudWatch alarms, WAF, and CI/CD that
builds the image into ECR instead of building on the instance.
