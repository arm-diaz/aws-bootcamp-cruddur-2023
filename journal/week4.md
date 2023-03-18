# Week 4 — Postgres and RDS

## Provision an RDS instance

To provision an RDS instance, I executed the following command in the CLI:

```sh
aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version  14.6 \
  --master-username cruddurroot \
  --master-user-password $PASSWORD \
  --allocated-storage 20 \
  --availability-zone us-east-1a \
  --backup-retention-period 0 \
  --port 5432 \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-deletion-protection

```

![Image of AWS RDS Create DB](assets/week4/cli-rds-create-db-instance.png)

After the command was executed, I waited until the DB changed to Available Status. This status means, it's ready to be used.

![Image of AWS RDS Available DB](assets/week4/aws-rds-available-db-instance.png)

## Temporarily stop an RDS instance

To stop a DB instance

+ In the navigation pane, choose Databases, and then choose the DB instance that you want to stop.
+ For Actions, choose Stop temporarily.
+ In the Stop DB instance temporarily window, select the acknowledgement that the DB instance will restart automatically after 7 days.

![Image of AWS RDS Stop DB](assets/week4/aws-rds-stopped-db-instance.png)

## Remotely connect to RDS instance

To connect to RDS instance, I used the CLI and VS Code Database Extension.

Run CLI command:

```sh
psql postgresql://cruddurroot:$PASSWORD@cruddur-db-instance.cimvlf2hk2ov.us-east-1.rds.amazonaws.com:5432/cruddur
```

![Image of SQL List DBs](assets/week4/sql-query-list-databases.png)

## Programmatically update a security group rule

To update a security group, I added ENV variables that extracts GITPOD IP Address and executes an AWS command.

ENV variables for security group ID and security rule id:

```sh
export DB_SG_ID="$MY_DB_SG_ID"
gp env DB_SG_ID="$MY_DB_SG_ID"
export DB_SG_RULE_ID="$MY_DB_SG_RULE_ID"
gp env DB_SG_RULE_ID="$MY_DB_SG_RULE_ID"
```

The command to update GITPOD IP Address can be found in `.gitpod.yml`:

```sh
export GITPOD_IP=$(curl ifconfig.me)
source  "$THEIA_WORKSPACE_ROOT/backend_flask/bin/rds-update-sg-rule"
```

![Image of CLI Update Security Group and Security Rule](assets/week4/cli-rds-update-sg-rule.png)

## Work with UUIDs and PSQL extensions

To create UUIDs, the `UUID` extension, `create table` command, and `drop table` command can be found in `backend_flask/db/schema.sql`.

We can execute the code in `schema.sql` using the following command:

```sh
psql cruddur < db/schema.sql -h cruddur-db-instance.cimvlf2hk2ov.us-east-1.rds.amazonaws.com -U cruddurroot
```

![Image of SQL extensions](assets/week4/sql-query-extension-create-table-list-tables.png)

## Troubleshoot common SQL errors

I did not get many errors during the implementation. However, to troubleshoot some of the few SQL errors, I used the docker logs to check any anomalies, inspected the browser, and checked CloudWatch logs.

For example, I got a timeout error after submitting confirmation code in Cruddur Sign-Up page.

![Image of Cruddur Confirmation Error](assets/week4/cruddur-confirmation-page-timeout-error.png)

After troubleshooting, I realized the lambda function was not connecting to the RDS VPC.

I also presented another error in the lambda function and I realized that a single quote was in the wrong place. This was an easy fix.

![Image of AWS Cloud Watch Lambda Error](assets/week4/aws-cloudwatch-log-error.png)

## Implement a Lambda that runs in a VPC and commits code to RDS

To create the lambda function and being able to commit code to RDS. I followed the next instructions:

+ Create Lambda Function
+ Add Environment variable: CONNECTION_URL
+ Connect to VPC default and Security Group default
+ Add Lambda layer using the ARN `arn:aws:lambda:us-east-1:898466741470:layer:psycopg2-py38:2`
+ In Cognito, create a lambda trigger using `Post confirmation Lambda trigger`.

Our lambda function looks like follows and can be found in `aws/lambda/cruddur-post-confirmation.py`.

```python
import os
import json
import psycopg2

def lambda_handler(event, context):
    user = event['request']['userAttributes']
    try:
        conn = psycopg2.connect(os.getenv('CONNECTION_URL'))
        cur = conn.cursor()
        user_display_name = user['name']
        user_email = user['email']
        user_handle = user['preferred_username']
        user_cognito_id = user['sub']
        cur.execute(f"INSERT INTO public.users (display_name, email, handle, cognito_user_id) VALUES('{user_display_name}', '{user_email}', '{user_handle}', '{user_cognito_id}')")
        conn.commit() 

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        
    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print('Database connection closed.')

    return event
```

![Image of AWS Lambda](assets/week4/aws-lambda-post-confirmation.png)

## Work with PSQL json functions to directly return json from the database

After signing-up and creating a post using the `Crud` button, we are able to populate information in our two tables.

The signing page populates the Users table that contains the following attributes:

+ uuid UUID
+ display_name text
+ handle text
+ email text
+ cognito_user_id text
+ created_at TIMESTAMP

![Image of Cruddur Sign Up](assets/week4/cruddur-signup.png)

![Image of SQL Users](assets/week4/sql-query-users-table.png)

The `Crud` button populates the Activities table that contains the following attributes:

+ uuid UUID
+ user_uuid
+ message text
+ replies_count integer
+ reposts_count integer
+ likes_count integer
+ reply_to_activity_uuid integer
+ expires_at TIMESTAMP
+ created_at TIMESTAMP

![Image of Cruddur Sign Up](assets/week4/cruddur-create-activity.png)

![Image of SQL Actitivies table](assets/week4/sql-query-actitivies-table.png)

## Fix: Time in Activity Content

I fixed the times displayed by the [Activity Content](https://github.com/arm-diaz/aws-bootcamp-cruddur-2023/blob/main/frontend-react-js/src/components/ActivityContent.js) for the functions `format_time_created_at` and `format_time_expires_at`. These two functions were displaying wrong times because the  `created_at` value is generated as UTC time but the function `DateTime.now()` gives the current time in your current local time zone. To fix the issue, I converted all times to time zone.

```javascript
DateTime.fromISO(value, {zone: 'utc'})
DateTime.now().setZone('utc')
```

For more information, please check the official documentation of the package `DateTime`:

+ [DateTime: Luxon Manual](https://moment.github.io/luxon/docs/class/src/datetime.js~DateTime.html#static-method-fromISO)
+ [DateTime: Some Luxon examples](https://moment.github.io/luxon/demo/global.html)

## Fix: Autofill email after signing up

I followed the post of one of the students to solve this issue. Please click on following link to see more details.

+ [Use Submitted Values across Different Pages in React.js](https://abdassalam.hashnode.dev/use-submitted-values-across-different-pages-in-reactjs)