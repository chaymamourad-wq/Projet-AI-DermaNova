# DermaNova — AI-Powered Skin Cancer Detection Platform

DermaNova is a medical web platform developed as part of an AI course project 
for first-year engineering students in Advanced Technologies at ENSTAB. 
It leverages deep learning (VGG16) to assist dermatologists in the early 
detection of skin cancer lesions.

---

## Screenshots

| Home | Dashboard | Result |
|------|-----------|--------|
| ![Home](screenshots/banner.png) | ![Dashboard](screenshots/dashboard.png) | ![Result](screenshots/result.png) |

---

## Features

- AI-powered skin lesion classification using a VGG16 convolutional neural network
- Doctor dashboard with patient record management
- Secure authentication system with hashed passwords
- Automated PDF medical report generation
- Admin panel for platform monitoring and user management
- Dual database support: SQLite for development, MySQL for production

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python 3.x, Flask 2.3             |
| AI Model   | TensorFlow 2.13, Keras, VGG16     |
| Frontend   | HTML5, CSS3, JavaScript           |
| Database   | SQLite / MySQL                    |
| PDF Export | ReportLab                         |
| Server     | Gunicorn                          |

---

## Getting Started

```bash
