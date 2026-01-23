from django.core.management.base import BaseCommand
from grc.models import AWSCredentials


class Command(BaseCommand):
    help = 'Set up AWS credentials in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--access-key',
            type=str,
            required=True,
            help='AWS Access Key ID'
        )
        parser.add_argument(
            '--secret-key',
            type=str,
            required=True,
            help='AWS Secret Access Key'
        )
        parser.add_argument(
            '--region',
            type=str,
            default='ap-south-1',
            help='AWS Region (default: ap-south-1)'
        )
        parser.add_argument(
            '--bucket-name',
            type=str,
            default='vardaanwebsites',
            help='S3 Bucket Name (default: vardaanwebsites)'
        )
        parser.add_argument(
            '--micro-service-url',
            type=str,
            default='http://13.233.147.73:3000/',
            help='Micro Service URL (default: http://13.233.147.73:3000/)'
        )

    def handle(self, *args, **options):
        try:
            # Check if credentials already exist
            existing_credentials = AWSCredentials.objects.first()
            
            if existing_credentials:
                # Update existing credentials
                existing_credentials.accessKey = options['access_key']
                existing_credentials.secretKey = options['secret_key']
                existing_credentials.region = options['region']
                existing_credentials.bucketName = options['bucket_name']
                existing_credentials.microServiceUrl = options['micro_service_url']
                existing_credentials.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated AWS credentials (ID: {existing_credentials.id})'
                    )
                )
            else:
                # Create new credentials
                credentials = AWSCredentials.objects.create(
                    accessKey=options['access_key'],
                    secretKey=options['secret_key'],
                    region=options['region'],
                    bucketName=options['bucket_name'],
                    microServiceUrl=options['micro_service_url']
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created AWS credentials (ID: {credentials.id})'
                    )
                )
            
            # Display the credentials (masking the secret key)
            credentials = AWSCredentials.objects.first()
            self.stdout.write('\nAWS Credentials Configuration:')
            self.stdout.write(f'Access Key: {credentials.accessKey}')
            self.stdout.write(f'Secret Key: {"*" * (len(credentials.secretKey) - 4) + credentials.secretKey[-4:]}')
            self.stdout.write(f'Region: {credentials.region}')
            self.stdout.write(f'Bucket Name: {credentials.bucketName}')
            self.stdout.write(f'Micro Service URL: {credentials.microServiceUrl}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up AWS credentials: {str(e)}')
            )
