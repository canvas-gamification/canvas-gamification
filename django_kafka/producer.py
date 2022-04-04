from kafka import KafkaProducer


def produce_question_created(question_id):
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
    print(producer)
    print(question_id)
    producer.send('QUESTION_CREATED', value=str(question_id).encode())


def produce_user_created(user_id):
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
    producer.send('USER:CREATED', value=str(user_id).encode())
