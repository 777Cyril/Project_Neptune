# Project_Neptune

# README

# Project Neptune - Beat Management and  Distribution System

Project Neptune is an innovative solution designed to streamline the distribution of musical beats to artists through an automated system that monitors a designated folder for new beats, manages metadata, and controls email distribution with a focus on improving placement opportunities.

## Features

- **Directory Monitoring**: Watches a user-specified directory for the creation of new MP3 files.
- **Beat Validation**: Validates new MP3 files to ensure they are not corrupt and meet the system's criteria.
- **Email Distribution**: Automatically sends validated beats to a list of recipients via email.
- **Queue System**: Utilizes a file queue system to manage and process beats in an organized fashion.
- **Logging**: Maintains a simple log of beats that have been processed and sent, along with timestamp and recipient information.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them:

- Python 3.x
- Pipenv or any virtual environment manager
- Flask
- Watchdog

## Installation

To set up Project Neptune on your local machine, follow these steps:

1. Clone the repository:
    
    ```bash
    git clone [repository-url]
    ```
    
2. Navigate to the project directory:
    
    ```bash
    bashCopy code
    cd Project_Neptune
    
    ```
    
3. Install the project dependencies using pipenv:
    
    ```bash
    bashCopy code
    pipenv install
    
    ```
    
4. Activate the virtual environment:
    
    ```bash
    bashCopy code
    pipenv shell
    
    ```
    
5. Run the application:
    
    ```bash
    bashCopy code
    python neptune.py
    
    ```

## **Folder Monitoring**

Project Neptune automatically watches a designated local folder for the appearance of new **`.mp3`** files using the **`watchdog`** library. When a new beat is detected, the system adds it to a processing queue for metadata extraction and email distribution.

## **Email Automation**

Upon processing, beats are queued and emailed to a curated list of artists based on genre, tempo, and other metadata to ensure the best match. Email sending is controlled to prevent server overload and ensure a smooth flow.

## **Usage**

Once the system is up and running, it will start monitoring the specified directory. Any MP3 files dropped into this directory will be automatically added to the processing queue and, upon validation, sent out to the list of recipients.

## **Built With**

- [Flask](http://flask.palletsprojects.com/) - The web framework used
- [Watchdog](https://pypi.org/project/watchdog/) - For monitoring directory changes
- [EyeD3](https://eyed3.readthedocs.io/en/latest/) - For handling MP3 metadata
