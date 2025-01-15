import os
import sys
import time
import fnmatch
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileMovedEvent, FileModifiedEvent

from monitor import monitor_network_connections, monitor_system_processes
from detector import AdvancedAnomalyDetector


def send_email_alert(subject, body, to_email):
    from_email = "vaishnavee0107@gmail.com"
    from_password = "urha pdqo lgeb ocls"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Set up the MIME message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Start TLS encryption
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print(f"Email alert sent to {to_email}.")
    except Exception as e:
        print(f"Error sending email: {e}")


class IDPSEventHandler(FileSystemEventHandler):
    def __init__(self, ignore_patterns=None, anomaly_detector=None, alert_email="vaishnaveepandey07@gmail.com"):
        super().__init__()
        self.ignore_patterns = ignore_patterns or []
        self.anomaly_detector = anomaly_detector
        self.alert_email = alert_email

    def _get_event_type(self, event):
        if isinstance(event, FileCreatedEvent):
            return 0
        elif isinstance(event, FileDeletedEvent):
            return 1
        elif isinstance(event, FileMovedEvent):
            return 2
        elif isinstance(event, FileModifiedEvent):
            return 3
        else:
            return -1

    def _get_event_vector(self, event):
        event_type = self._get_event_type(event)
        if event_type == -1:
            return None

        file_size = 0
        if os.path.exists(event.src_path):
            file_size = os.path.getsize(event.src_path)

        return [event_type, file_size]

    def should_ignore(self, path):
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def log_event(self, event_type, path):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        with open("./logs/file_log.txt", "a") as log_file:
            log_file.write(f"{timestamp} - {event_type} - {path}\n")

        # Send email alert when an event occurs
        subject = f"Intrusion Detection Alert: {event_type.capitalize()} Event"
        body = f"Event Type: {event_type.capitalize()}\nFile: {path}\nTimestamp: {timestamp}"
        send_email_alert(subject, body, self.alert_email)

    def on_created(self, event):
        if self.should_ignore(event.src_path):
            return
        feature_vector = self._get_event_vector(event)
        if feature_vector is not None:
            self.anomaly_detector.add_event(feature_vector)
        print(f"Alert! {event.src_path} has been created.")
        self.log_event("created", event.src_path)

    def on_deleted(self, event):
        if self.should_ignore(event.src_path):
            return
        feature_vector = self._get_event_vector(event)
        if feature_vector is not None:
            self.anomaly_detector.add_event(feature_vector)
        print(f"Alert! {event.src_path} has been deleted.")
        self.log_event("deleted", event.src_path)

    def on_moved(self, event):
        if self.should_ignore(event.src_path) and self.should_ignore(event.dest_path):
            return
        feature_vector = self._get_event_vector(event)
        if feature_vector is not None:
            self.anomaly_detector.add_event(feature_vector)
        print(f"Alert! {event.src_path} has been moved to {event.dest_path}.")
        self.log_event("moved", f"{event.src_path} -> {event.dest_path}")

    def on_modified(self, event):
        if self.should_ignore(event.src_path):
            return
        feature_vector = self._get_event_vector(event)
        if feature_vector is not None:
            self.anomaly_detector.add_event(feature_vector)
        print(f"Alert! {event.src_path} has been modified.")
        self.log_event("modified", event.src_path)


def main():
    paths = ["./lab"]
    ignore_patterns = ["*.tmp", "*.log"]
    anomaly_detector = AdvancedAnomalyDetector(threshold=10, time_window=60)
    alert_email = "vaishnaveepandey07@gmail.com"
    event_handler = IDPSEventHandler(ignore_patterns=ignore_patterns, anomaly_detector=anomaly_detector, alert_email=alert_email)
    observer = Observer()

    for path in paths:
        observer.schedule(event_handler, path, recursive=True)

    observer.start()

    network_monitor_thread = threading.Thread(target=monitor_network_connections)
    network_monitor_thread.start()

    process_monitor_thread = threading.Thread(target=monitor_system_processes)
    process_monitor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    network_monitor_thread.join()
    process_monitor_thread.join()

if __name__ == "__main__":
    main()