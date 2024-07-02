import boto3

# Crear un cliente de DynamoDB
dynamodb = boto3.client('dynamodb', region_name='us-east-1')

try:
    # Crear la tabla
    response = dynamodb.create_table(
        TableName='FeaturedDocuments',
        KeySchema=[
            {
                'AttributeName': 'DocumentoID',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'DocumentoID',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print("Tabla creada con éxito!")
except Exception as e:
    print("Error al crear la tabla:")
    print(e)
