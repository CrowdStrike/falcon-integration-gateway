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
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            raise Exception(f"SecretString not found in the response for secret ({secret_name})")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                raise Exception(f"The requested secret ({secret_name}) was not found") from e
            if error_code == 'InvalidRequestException':
                raise Exception(f"The request was invalid due to: {e}") from e
            if error_code == 'InvalidParameterException':
                raise Exception(f"The request had invalid params: {e}") from e
            raise Exception(f"Error retrieving Secrets Manager secret ({secret_name}): {e}") from e

    def validate_secret_keys(self, secret, client_id_key, client_secret_key):
        """Validate the presence of required keys in the secret."""
        falcon_client_id = secret.get(client_id_key)
        falcon_client_secret = secret.get(client_secret_key)

        if falcon_client_id is None:
            raise Exception(f"The client ID key ({client_id_key}) does not exist or is None in the retrieved secret.")
        if falcon_client_secret is None:
            raise Exception(f"The client secret key ({client_secret_key}) does not exist or is None in the retrieved secret.")

        return falcon_client_id, falcon_client_secret

    def load_credentials(self, store):
        """Load credentials based on the specified store."""
        if store == 'ssm':
            ssm_client = boto3.client('ssm', region_name=self.region)
            falcon_client_id = self.get_ssm_parameter(
                ssm_client,
                self.config.get('ssm', 'ssm_client_id')
            )
            falcon_client_secret = self.get_ssm_parameter(
                ssm_client,
                self.config.get('ssm', 'ssm_client_secret')
            )
        elif store == 'secrets_manager':
            secrets_client = boto3.client('secretsmanager', region_name=self.region)
            secret = self.get_secret(
                secrets_client,
                self.config.get('secrets_manager', 'secrets_manager_secret_name')
            )
            falcon_client_id, falcon_client_secret = self.validate_secret_keys(
                secret,
                self.config.get('secrets_manager', 'secrets_manager_client_id_key'),
                self.config.get('secrets_manager', 'secrets_manager_client_secret_key')
            )
        else:
            raise ValueError("Invalid credentials store specified.")

        return falcon_client_id, falcon_client_secret
