import json
import boto3
from botocore.exceptions import ClientError


class CredStore:
    def __init__(self, config, region):
        self.config = config
        self.region = region

    def get_ssm_parameter(self, client, parameter_name):
        """Retrieve a parameter from AWS SSM Parameter Store."""
        try:
            response = client.get_parameter(Name=parameter_name, WithDecryption=True)
            return response['Parameter']['Value']
        except ClientError as e:
            raise Exception(f"Error retrieving SSM parameter ({parameter_name}): {e}") from e

    def get_secret(self, client, secret_name):
        """Retrieve a secret from AWS Secrets Manager."""
        try:
            response = client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            raise Exception(f"Error retrieving Secrets Manager secret ({secret_name}): {e}") from e

    def load_credentials(self, store):
        """Load credentials based on the specified store."""
        if store == 'ssm':
            ssm_client = boto3.client('ssm', region_name=self.region)
            falcon_client_id = self.get_ssm_parameter(
                ssm_client,
                self.config.get('credentials_store', 'ssm_client_id')
            )
            falcon_client_secret = self.get_ssm_parameter(
                ssm_client,
                self.config.get('credentials_store', 'ssm_client_secret')
            )
        elif store == 'secrets_manager':
            secrets_client = boto3.client('secretsmanager', region_name=self.region)
            secret = self.get_secret(
                secrets_client,
                self.config.get('credentials_store', 'secrets_manager_secret_name')
            )
            falcon_client_id = secret.get(
                self.config.get('credentials_store', 'secrets_manager_client_id_key')
            )
            falcon_client_secret = secret.get(
                self.config.get('credentials_store', 'secrets_manager_client_secret_key')
            )
        else:
            raise ValueError("Invalid credentials store specified.")

        return falcon_client_id, falcon_client_secret
