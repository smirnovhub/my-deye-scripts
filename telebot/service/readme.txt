############################################################
### how to check logs in case of crash or something else ###
############################################################

service telebot logs

OR

service telebot logs 100

OR

journalctl -u telebot.service --no-pager | tail -n 30

##################################################
### how to run bot as service with autorestart ###
##################################################

bot will be automatically restarted in the case of the crash!

fix pathes to actual in /etc/systemd/system/telebot.service:
WorkingDirectory=/home/dmitry/git/scripts/deye/telebot
ExecStart=/home/dmitry/git/scripts/deye/telebot/telebot

copy files to:
/etc/init.d/telebot
/etc/systemd/system/telebot.service

then run commands:
systemctl daemon-reload
systemctl enable telebot
systemctl start telebot

systemctl status telebot
output:
  ● telebot.service - Telegram bot
     Loaded: loaded (/etc/systemd/system/telebot.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2025-09-01 16:50:18 EEST; 1min 15s ago
   Main PID: 321 (telebot)
      Tasks: 4 (limit: 4915)
     CGroup: /system.slice/telebot.service
             └─321 /usr/bin/python3.8 /home/dmitry/git/scripts/deye/telebot/telebot
  
  Sep 01 16:50:18 Ubuntu-HTTP-172-17-17-2 systemd[1]: Started Telegram bot.

systemctl is-enabled telebot
output:
  enabled

also you can use command:
service telebot status (start, stop, etc.)
