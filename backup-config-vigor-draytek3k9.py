
import requests
import os
import sys
from netmiko import ConnectHandler
import time
from datetime import datetime, timedelta
from netmiko.ssh_exception import NetMikoTimeoutException,NetMikoAuthenticationException
from paramiko.ssh_exception import SSHException
import subprocess

vigor_draytek_3900 = {
    'device_type': 'cisco_ios',
    'host':   '192.168.1.1',
    'username': 'admin',
    'password': 'admin',
    'port' : 22,
    'secret': 'admin',
}

def _get_ymd_currently():

    ymd = datetime.now()
    YMD = ymd.strftime("%Y%m%d")
    return YMD

def _get_hms_currently():

    hms = datetime.now()
    HMS = hms.strftime("%H%M%S")
    return HMS

def _create_new_folder_tftp():
    
    year_month_day = _get_ymd_currently()
    folder_mkdir = '/tftpdata/router1-vigor-draytek3k9/config-'+year_month_day
    os.system("mkdir -p "+folder_mkdir)
    print('Create mkdir folder '+folder_mkdir+' complete....')

def _chown_permissions_folder_tftp():

    folder_chown = '/tftpdata/router1-vigor-draytek3k9/'
    os.system("chown -R tftp:tftp "+folder_chown)
    print('chown user tftp:tftp folder '+folder_chown+' complete....')

def _chmod_permissions_folder_tftp():

    year_month_day = _get_ymd_currently()
    folder_chmod = '/tftpdata/router1-vigor-draytek3k9/'   
    os.system("chmod -R 777 "+folder_chmod)
    os.system("chmod -R 777 "+folder_chmod+'*')
    print('Permissions chmod -R 777 '+folder_chmod+' complete....')

def _remove_old_folder_tftp():

    for ago_days in range(30,60):
        date_days_ago = (datetime.now() - timedelta(days=ago_days)).strftime("%Y%m%d")
        get_date_time_ago = "/tftpdata/router1-vigor-draytek3k9/config-"+date_days_ago
        os.system("rm -rf "+get_date_time_ago)
        print('Running cmd rm -rf '+get_date_time_ago)

def send_api_telegram_bot_failed(CONTENT_DETAIL):

    STRING_TOKEN_HTTP_API_BOT_FAILED = 'copy and paste token here'
    SEND_MESSAGE_BOT_FAILED = '/sendMessage'
    HTTPS_API_TELEGRAM_BOT_FAILED = 'https://api.telegram.org/bot'
    API_TELEGRAM_BOT_FAILED = HTTPS_API_TELEGRAM_BOT_FAILED + STRING_TOKEN_HTTP_API_BOT_FAILED + SEND_MESSAGE_BOT_FAILED
    CHAT_ID = '-123456789'
    header={'Content-Type': 'application/json'}
    body="""{
                    "chat_id":\""""+str(CHAT_ID)+"""\",
                    "text":\""""+CONTENT_DETAIL+"""\"
                    }"""
    result = requests.post(API_TELEGRAM_BOT_FAILED,data=body,headers=header,timeout=60)
    return result.content

def send_api_telegram_bot_true(CONTENT_DETAIL):

    STRING_TOKEN_HTTP_API_BOT_TRUE = 'copy and paste token here'
    SEND_MESSAGE_BOT_TRUE = '/sendMessage'
    HTTPS_API_TELEGRAM_BOT_TRUE = 'https://api.telegram.org/bot'
    API_TELEGRAM_BOT_TRUE = HTTPS_API_TELEGRAM_BOT_TRUE + STRING_TOKEN_HTTP_API_BOT_TRUE + SEND_MESSAGE_BOT_TRUE
    CHAT_ID = '-123456789'

    header={'Content-Type': 'application/json'}
    body="""{
                    "chat_id":\""""+str(CHAT_ID)+"""\",
                    "text":\""""+CONTENT_DETAIL+"""\"
                    }"""
    result = requests.post(API_TELEGRAM_BOT_TRUE,data=body,headers=header,timeout=60)
    return result.content

def _backup_config_to_tftp_server():
    
    year_month_day = _get_ymd_currently()
    hour_munites_second = _get_hms_currently()
    mode_enable = 'enable'
    mode_configure_system = 'configure system'
    file_name_router_backup = '192.168.1.1-V3900-1.5.1-'+year_month_day+'-'+hour_munites_second+'.tgz'
    command_backup_file_config_tftp = 'config backup 192.168.1.3 '+file_name_router_backup  
    path_sub_directory_tftp_server = '/router1-vigor-draytek3k9/config-'+year_month_day+'/'
    start_time = datetime.now()
    try:
        net_connect_device = ConnectHandler(**vigor_draytek_3900)
        net_connect_device.enable()


        result_run_command = net_connect_device.send_command(mode_enable, expect_string=r'Entering enable mode...')
        result_run_command += net_connect_device.send_command(mode_configure_system, expect_string=r'#')
        result_run_command += net_connect_device.send_command(command_backup_file_config_tftp, expect_string=r'#')
        print(result_run_command)
        print(file_name_router_backup)
        time.sleep(10)
        print(file_name_router_backup)
        end_time = datetime.now()
        print("Total time backup startup config: {}".format(end_time - start_time))

        CONTENT_DETAIL = '#BackupConfig #RouterVigor #Draytek3900 #TftpServer #Done\nIP Router: 192.168.1.1\nJob status: Ok\n'
        send_api_telegram_bot_true(CONTENT_DETAIL)
        net_connect_device.disconnect()
        command_move_backup_file_config_tftp='mv /tftpdata/192.168.1.1-V3900-1.5.1-* /tftpdata'+path_sub_directory_tftp_server
        os.system(command_move_backup_file_config_tftp)
    except NetMikoTimeoutException as error:
        CONTENT_DETAIL = '#BackupConfig #RouterVigor #Draytek3900 #TftpServer #ConnectingTimeOut\nIP Router: 192.168.1.1\nJob status: Failed\n'
        CONTENT_DETAIL += str(error)
        send_api_telegram_bot_failed(CONTENT_DETAIL)
        return None
    except NetMikoAuthenticationException as error:

        CONTENT_DETAIL = '#BackupConfig #RouterVigor #Draytek3900 #TftpServer #AuthenticationFailed\nIP Router: 192.168.1.1\nJob status: Failed\n'
        CONTENT_DETAIL += str(error)
        send_api_telegram_bot_failed(CONTENT_DETAIL)
        return None

def _switch_force_error_via_exit_code(process_exit_code):

    switcher = {
        0: 'rsync exit codes '+ str(process_exit_code) +': Success',
        1: 'rsync exit codes '+ str(process_exit_code) +': Syntax or usage error',
        2: 'rsync exit codes '+ str(process_exit_code) +': Protocol incompatibility',
        3: 'rsync exit codes '+ str(process_exit_code) +': Errors selecting input/output files, dirs',
        4: 'rsync exit codes '+ str(process_exit_code) +': Requested  action not supported: an attempt was made to manipulate 64-bit files on a platform that cannot support them; or an option was specified that is supported by the client and not by the server',
        5: 'rsync exit codes '+ str(process_exit_code) +': Error starting client-server protocol',
        6: 'rsync exit codes '+ str(process_exit_code) +': Daemon unable to append to log-file',
        10: 'rsync exit codes '+ str(process_exit_code) +': Error in socket I/O',
        11: 'rsync exit codes '+ str(process_exit_code) +': Error in file I/O',
        12: 'rsync exit codes '+ str(process_exit_code) +': Error in Rsync protocol data stream',
        13: 'rsync exit codes '+ str(process_exit_code) +': Errors with program diagnostics',
        14: 'rsync exit codes '+ str(process_exit_code) +': Error in IPC code',
        20: 'rsync exit codes '+ str(process_exit_code) +': Received SIGUSR1 or SIGINT',
        21: 'rsync exit codes '+ str(process_exit_code) +': Some error returned by waitpid()',
        22: 'rsync exit codes '+ str(process_exit_code) +': Error allocating core memory buffers',
        23: 'rsync exit codes '+ str(process_exit_code) +': Partial transfer due to error',
        24: 'rsync exit codes '+ str(process_exit_code) +': Partial transfer due to vanished source files',
        25: 'rsync exit codes '+ str(process_exit_code) +': The --max-delete limit stopped deletions',
        30: 'rsync exit codes '+ str(process_exit_code) +': Timeout in data send/receive',
        35: 'rsync exit codes '+ str(process_exit_code) +': Timeout waiting for daemon connection',
        127: 'rsync exit codes '+ str(process_exit_code) +': Dont even have rsync binary installed on your system.',
        255: 'rsync exit codes '+ str(process_exit_code) +': SSH could not resolve hostname name or service not known',
    }
    return switcher.get(process_exit_code, 'nothing')

def _start_rsync_config_to_nas():

    year_month_day = _get_ymd_currently()
    path_save_config_switch = '/tftpdata/router1-vigor-draytek3k9'
    REMOTE_PASSWORD_USER = 'rsync'
    REMOTE_PORT = '8222'
    REMOTE_USER = 'rsync'
    REMOTE_HOST = '192.168.1.2'
    REMOTE_PATH_FOLDER_BACKUP_DATASOURCE_NAS = '/Backup/'
    
    VALUE_LOOP_RUNNING_RSYNC = 1
    while VALUE_LOOP_RUNNING_RSYNC < 5:
        VALUE_LOOP_RUNNING_RSYNC += 1

        rsync_select_option = '-av --progress --delete'
        rsync_select_ssh_remote = '--rsh="sshpass -p'+REMOTE_PASSWORD_USER+' ssh -p'+REMOTE_PORT+' -oStrictHostKeyChecking=no"'
        rsync_infor_ssh_remote = REMOTE_USER+'@'+REMOTE_HOST+':'+REMOTE_PATH_FOLDER_BACKUP_DATASOURCE_NAS
        command_run_rsync = 'rsync '+rsync_select_option+' '+rsync_select_ssh_remote+' '+path_save_config_switch+' '+rsync_infor_ssh_remote
       
        print('cmd running: '+command_run_rsync)
        process_exit_code = subprocess.call(command_run_rsync, shell=True)
        if process_exit_code == 0:
            status_job_rsync = _switch_force_error_via_exit_code(process_exit_code)
            print(status_job_rsync)
            CONTENT_DETAIL = '#RsyncConfig #NAS #RouterVigor #Draytek3900 #Successful \nIP Router: 192.168.1.1\nJob status: Ok\n'
            CONTENT_DETAIL += status_job_rsync
            send_api_telegram_bot_true(CONTENT_DETAIL)
            break
        else:
            status_job_rsync = _switch_force_error_via_exit_code(process_exit_code)
            print(status_job_rsync)
            CONTENT_DETAIL = '#RsyncConfig #NAS #RouterVigor #Draytek3900 #UnSuccessful \nIP Router: 192.168.1.1\nJob status: Failed\n'
            CONTENT_DETAIL += status_job_rsync
            send_api_telegram_bot_failed(CONTENT_DETAIL)


if __name__ == '__main__':
    _create_new_folder_tftp()
    _chown_permissions_folder_tftp()
    _chmod_permissions_folder_tftp()
    _backup_config_to_tftp_server()
    time.sleep(5)
    _remove_old_folder_tftp()
    time.sleep(5)
    _start_rsync_config_to_nas()
