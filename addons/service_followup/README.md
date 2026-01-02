# Service Follow-up

Track customer feedback after appointments and never miss a follow-up again.

## What it does

After a service appointment, you want to check in with your customers. Did everything go well? Are they satisfied? This module helps you stay on top of those follow-ups without letting them slip through the cracks.

You can create a follow-up record, mark when you've sent it out, and log the customer's response including a 1-10 rating and any comments they give you. If two days pass without a reply, the system automatically creates a reminder activity so you don't forget to check back in.

### Features

- Track follow-ups with your customers after appointments
- Simple workflow: Draft → Sent → Replied → Closed
- Record customer ratings (1-10) and feedback
- Automatic reminders if you haven't heard back in 2 days
- Built-in chatter for keeping notes and communication history
- Activity notifications to keep team members in the loop

## Installation

You'll need Odoo 19.0. If you're using Docker (recommended):

1. **Create a config file** at `config/odoo.conf`:

```ini
[options]
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
```

> **Note:** Odoo will generate an admin password automatically on first run and display it in the logs. You can also set your own by adding `admin_passwd = your_password` to the config.

2. **Make sure your `docker-compose.yml` mounts the folders**:

```yaml
services:
  odoo:
    image: odoo:19.0
    volumes:
      - ./addons:/mnt/extra-addons
      - ./config:/etc/odoo
```

3. **Start Odoo**:

```bash
docker compose up -d
```

4. **Install the module** - go to `http://localhost:8069`, log in as admin, and:

- Go to **Apps**
- Click **Update Apps List** (turn on Developer Mode if you don't see this)
- Search for **"Service Follow-up"**
- Click **Install**

## Usage

### Creating a follow-up

1. Open **Follow-ups** → **All Follow-ups**
2. Click **Create**
3. Fill in the subject, customer, appointment date, and who's handling it
4. Save

### Workflow

- **Mark Sent** - Click when you've reached out to the customer (timestamps automatically)
- **Log Reply** - Customer got back to you? Mark it as replied and add their rating/feedback
- **Close** - Done with this follow-up? Close it out

### Automatic reminders

A daily scheduled action checks for follow-ups sent more than 2 days ago without a response. It creates a TODO activity for the assigned user. It won't create duplicates if one already exists.

## Development

### Updating the module

After code changes:

```bash
docker compose restart odoo
docker compose exec odoo odoo -u service_followup -d <database_name> --stop-after-init
```

Or upgrade from the UI: **Apps** → find the module → **Upgrade**

### Running tests

```bash
docker compose exec odoo odoo --test-enable --test-tags=service_followup -d <database_name> --stop-after-init
```

### Module structure

```
service_followup/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── followup.py
├── views/
│   └── followup_views.xml
├── security/
│   └── ir.model.access.csv
├── data/
│   └── ir_cron.xml
├── tests/
│   ├── __init__.py
│   └── test_followup.py
└── README.md
```

## Troubleshooting

### Module not showing in Apps

- Check that the addon folder is mounted at `/mnt/extra-addons` in the container
- Verify `addons_path` in `odoo.conf` includes `/mnt/extra-addons`
- Update the apps list (requires Developer Mode)

### Tests failing

- Use a clean test database

### Cron not running

- Check **Settings** → **Technical** → **Scheduled Actions**
- Click **Run Manually** to test it
- Check Odoo logs for errors

### Permission errors

- User needs to be in the `base.group_user` group
- Check `ir.model.access.csv` for access rights

## Technical details

Model: `service.followup`

Inherits: `mail.thread`, `mail.activity.mixin`

**Fields:**

- `name` - Subject (required)
- `partner_id` - Customer (required)
- `appointment_date` - When the appointment was
- `assigned_user_id` - Who's responsible
- `state` - Draft/Sent/Replied/Closed
- `sent_at`, `replied_at` - Timestamps
- `rating` - 1-10 rating (validated)
- `feedback` - Customer comments
- `chatbot_summary` - Extra notes

**Methods:**

- `action_mark_sent()` - Transition to sent state
- `action_log_reply()` - Transition to replied state
- `action_close()` - Close the follow-up
- `cron_followup_reminder()` - Creates reminder activities

## License

LGPL-3

## Author

github.com/onuriscoding

## Version

19.0.1.0.0
