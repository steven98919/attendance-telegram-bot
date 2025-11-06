# Attendance Telegram Bot

A Telegram bot for employee attendance monitoring and reporting. Retrieves data from attendance machines (via database) and generates automated reports with data visualization.

## Overview

This bot is designed to work with attendance data from **Revo FF-162BNC** fingerprint attendance machine. The attendance data is first imported to a database using the **Easylink SDK** Windows application, then this bot queries the database to generate reports and visualizations.

## System Architecture

```
Revo FF-162BNC → Easylink SDK (Windows) → MySQL Database → Telegram Bot → Reports/Visualizations
```

## Features

- 📊 Automated attendance reports
- 📈 Data visualization (charts, graphs)
- 📄 Export reports to PDF/Excel
- 🔔 Real-time attendance monitoring
- 👥 Admin management system
- 📅 Custom date range queries
- 💼 Employee attendance tracking
- 📝 Leave/absence management

## Requirements

- Python 3.x
- MySQL Database
- Telegram Bot Token
- Revo FF-162BNC attendance machine
- Easylink SDK (for data import from device to database)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/attendance-telegram-bot.git
cd attendance-telegram-bot
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

4. Edit `.env` file with your credentials:
```env
BOT_API = 'your_telegram_bot_api_token'
DATABASE_USER = 'your_database_user'
DATABASE_PASSWORD = 'your_database_password'
DATABASE_IP = 'your_database_ip'
DATABASE_ONE = 'database_name'
DATABASE_TWO = 'attendance_database'
TELEBOT_ID_ADMIN = admin_user_id_1,admin_user_id_2
```

## Configuration

### 1. Setup Attendance Machine
- Configure your **Revo FF-162BNC** device
- Register employees' fingerprints on the device

### 2. Import Data to Database
- Use **Easylink SDK** Windows application to:
  - Connect to your Revo FF-162BNC device
  - Import attendance data to MySQL database
  - Configure automatic sync (recommended)

### 3. Setup Telegram Bot
- Create a bot via [@BotFather](https://t.me/botfather)
- Get your bot token
- Add the token to `.env` file

## Usage

Run the bot:
```bash
python main.py
```

### Bot Commands

- `/start` - Start the bot
- `/help` - Show available commands
- `/report` - Generate attendance report
- `/today` - Today's attendance
- `/summary` - Monthly summary
- `/export` - Export data to Excel/PDF

## Database Schema

The bot expects the following database structure from Easylink SDK:

- Employee information table
- Attendance records table
- Leave/absence records table

(Configure according to your Easylink SDK database output)

## Modules

- `main.py` - Main bot application
- `db.py` - Database operations
- `helper.py` - Helper functions
- `ModulPdf/` - PDF generation module
- `ModulExcel/` - Excel export module
- `ModulGenerateCuti/` - Leave management module
- `ModulSummary/` - Summary report generator

## Security Notes

⚠️ **Important**:
- Never commit your `.env` file
- Keep your bot token secure
- Restrict admin access to trusted users only
- Use strong database passwords
- Regularly backup your database

## Troubleshooting

### Bot not responding
- Check if bot is running: `ps aux | grep main.py`
- Verify bot token is correct
- Check internet connection

### Database connection error
- Verify database credentials in `.env`
- Check if MySQL service is running
- Verify database IP and port accessibility

### Easylink SDK sync issues
- Check device connection
- Verify network settings on Revo FF-162BNC
- Restart Easylink SDK service

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- Telegram Bot API
- Revo FF-162BNC fingerprint attendance machine
- Easylink SDK for data synchronization
