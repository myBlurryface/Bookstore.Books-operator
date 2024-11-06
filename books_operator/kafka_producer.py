from confluent_kafka import Producer


config = {
    'bootstrap.servers': 'kafka:9092',
}


def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

producer = Producer(config)

def send_message(topic, message):
    producer.produce(topic, value=message, callback=delivery_report)
    producer.flush()
