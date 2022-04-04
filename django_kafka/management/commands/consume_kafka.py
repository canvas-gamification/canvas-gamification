from django.core.management import BaseCommand
from kafka import KafkaConsumer

from django_kafka.consumer import consume


class Command(BaseCommand):
    help = 'Consumes Kafka messages'

    def handle(self, *args, **options):
        consumer = KafkaConsumer(
            bootstrap_servers=['localhost:9092']
        )
        consumer.subscribe(pattern='.*')
        for message in consumer:
            try:
                consume(message)
            except Exception as e:
                print(e)
