'''
Created on Apr 30, 2021

@author: xt153g
'''
from invoke import run
import logging,re,socket,configparser
import datetime

callback_log_path = "/var/log/ATE/callback/callback.err"
consumer_valid_time_range = 60*60 # 60 mins
logging.basicConfig(filename='oam_recovery.log', level=logging.INFO, format='%(asctime)s:- %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]')

def time_compare(cur_time,prev_time,time_threshold):
    # function to compare the timestamp to make sure cur_time - prev_time <= time_threshold
    # return type Bool
    # use datetime pbj and datetime delta obj
    logging.info("cur is %s, prev is %s, diff is %s",cur_time,prev_time,(cur_time - prev_time).seconds)
    if (cur_time - prev_time).seconds < time_threshold:
        return True
    return False


def fetch_timestamp_from_log(output,pattern):
    # if pattern existing in output , return its timestamp
    #pattern = "Sending post request for message"
    timestamps = []
    temp = []
    for op in output:
        if pattern in op:
            # 2021-05-06 22:06:11 UTC
            timestamp = re.search(r"\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}",op)
            if timestamp:
                temp.append(timestamp.group())

    if temp:
        for timestamp in temp:
            # convert all time stamp from string to UTC time
            date_time_obj = datetime.datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S")
            timestamps.append(date_time_obj)

    return timestamps


# === Celery Service hung recovery part ==============================================================================
''' 
   1) if last line contains [missed heartbeat] and we have queued tasks in RMQ, restart this celery service
   2) if last line contains [missed heartbeat] but no queued tasks in RMQ, then check if the time stamp of this last line is 1 hour ago
   restart celery service if it's beyond 1 hour
   3) Otherwise, do nothing

'''
#=====================================================================================================================
def recover_celery_service():
    rmq_queue_cmd = "rabbitmqctl list_queues -p celery | grep priority_high_long"
    log_celery_cmd = "tail -1 /var/log/ATE/celery/celeryd.err | grep 'missed heartbeat'"
    res_log,res_queue_task = None,None
    task_num = 0
    time_stamp_list = []

    try:
        res_log = run(log_celery_cmd)
    except Exception as e:
        # if exception happens, means log_celery_cmd did not find anything. mostly the celery is working fine.
        logging.error("Can't get the sign for exceptional case, will skip the recovery process ... :- [%s]",current_host,e)
        return

    if res_log is not None:
        time_stamp_list.append(res_log.stdout)
        time_stamp_list = fetch_timestamp_from_log(time_stamp_list,"missed heartbeat")

    try:
        res_queue_task = run(rmq_queue_cmd)
    except Exception as e:
        logging.error("Can't get the tasks number in queue priority_high_long, can only skip this recovery process... :- [%s]",e)
        return

    if not res_queue_task.stderr and res_queue_task.stdout is not None:
        task_num = re.split('\t|\n',res_queue_task.stdout)[1]  #['priority_high_long', '0', '']


    if len(time_stamp_list) > 0:
        if int(task_num) > 0 or not time_compare(datetime.datetime.utcnow(), time_stamp_list[0], consumer_valid_time_range):
            logging.error("Encountered the missed heartbeat at last line, queued task is %s, time stamp is %s, will restart celery service to fix the hung workers",task_num,time_stamp_list[0])
            action_cmd = "/ENV2.7/bin/supervisorctl -c /etc/supervisord.worker restart celery"
            try:
                res = run(action_cmd)
                if "celery: started" not in res.stdout:
                    logging.error("Celery restart failed, please check it manually.")
            except Exception as e:
                logging.error("Received exception when restart the celery service - [%s]",e)
                return
    else:
        logging.info("No sign for exceptions, queued task is %s and log result is [%s]",task_num,res_log.stdout)


# === Callback Service recovery part =================================================================================
'''
Check Callback service log to identify whether there is any sign for out-of-service
'''
#=====================================================================================================================
def recover_callback_service():
    callback_queue_res,anchor1_res,anchor2_res=None,None,None
    rmq_callback_queue = "rabbitmqctl list_queues -p celery | grep callback_queue"
    log_callback_comsumer_cmd = "tail -50 " + callback_log_path + " | grep 'Sending post request' -B 5 -A 5"
    anchor1_cmd = "tail -50 " + callback_log_path + " | grep 'Declaring queue callback_queue'"
    anchor2_cmd = "tail -50 " + callback_log_path + " | grep 'Adding consumer cancellation callback'"
    #log_callback_publisher_cmd = "tail -50 /var/log/ATE/celery/callback_in_exec.log | grep 'Publish could not be confirmed'"
    rebuild_callback_queue = "rabbitmqctl eval 'Q = {resource, <<\"celery\">>, queue, <<\"callback_queue\">>}, rabbit_amqqueue:internal_delete(Q, <<\"CLI\">>).'"
    restart_callback = "/ENV2.7/bin/supervisorctl -c /etc/supervisord.web restart callback"
    is_callback_queue_ok = False

    # Recover Function
    def callback_recover(is_callback_queue_ok=False):
        try:
            restart_res = run(restart_callback)
        except Exception as e:
            logging.error("Received exception to restart callback consumer service for ATE %s, [%s]",current_host,e)
            return False
        if "callback: started" not in restart_res.stdout:
            logging.error("call back service can not be restarted successfully")
            return False
        if not is_callback_queue_ok:
            try:
                rebuild_queue_res = run(rebuild_callback_queue)
            except Exception as e:
                logging.error("Received exception to re-build the callback queue for ATE %s, [%s]",current_host,e)
                return False

        logging.info("Recover is done and successful!")
        return True

    # 1) Get the result that if this queue is there
    # callback_queue    0
    # 'callback_queue\t0\n
    try:
        callback_queue_res = run(rmq_callback_queue)
    except Exception as e:
        logging.error("Received exception to get callback queue status for ATE %s - [%s], RMQ or this Queue must be in problem, will skip...",current_host,e)
    if callback_queue_res and "callback_queue" in callback_queue_res.stdout:
        logging.info("Callback queue is running correctly, reserving it for next checking step...")
        is_callback_queue_ok = True


    # 2) Analyzing the key words to confirm if it's not working right in latest half hour.
    # INFO       2021-04-27 16:42:59,682 __main__        setup_queue           204 : Declaring queue callback_queue
    # ...
    # is it : INFO       2021-04-27 16:43:41,119 __main__        add_on_cancel_callback  257 : Adding consumer cancellation callback
    # or not above correct subsequent log
    try:
        anchor1_res = run(anchor1_cmd)
    except Exception as e:
        # the consumer service is fine because patter 'Declaring queue callback_queue' is not showing.
        logging.error("Failed to get anchor #1 of callback consumer service for ATE %s, will skip now ...! :-[%s]",current_host,e)
        return

    # check anchor 2 further while we found the anchor 1
    if anchor1_res:
        if anchor1_res.stderr:
            logging.error("Command to check consumer call back is failing for ATE %s, failure reason is %s" %(current_host, anchor1_res.stderr))

        # start to parsing log. Check if the error is happening in last 30 mins ( not 1hour ago, not yesterday , not 2days ago)
        # Maybe we do not need set this time line for our checking
        output = anchor1_res.stdout.split(r"\n")
        pattern2 = 'Declaring queue callback_queue'
        time_stamp2_list = fetch_timestamp_from_log(output,pattern2)
        now = datetime.datetime.utcnow()

        callback_error_times = []
        for time_stamp in time_stamp2_list:
            if time_compare(now,time_stamp,consumer_valid_time_range):
                callback_error_times.append(time_stamp)

        if len(callback_error_times) == 0:
            logging.warning("The time stamp of anchor 1 is out of range, we can skip now ...")
            return

        # since we suspect there is call back error now .  check below conditions
        # Anchor2 - check 'Adding consumer cancellation callback' existing or not.
        # if Anchor2 existing but is_callback_queue_ok = True -> restart call_back queue only
        # else check cond1 and cond2 -> if either True, consider as working
        # conditon1 : empty lines after 'Adding consumer cancellation callback'  --- working
        # condition2: 'Adding consumer cancellation callback' existing and shows up within 2min of time that 'Declaring queue callback_queue' show up
        #             and we can see the right key word following up after anchor #2

        # Anchor 2
        try:
            anchor2_res = run(anchor2_cmd)
        except Exception as anchor2_err:
            logging.error("Anchor #2 in callback log could not be found, callback service is in wrong state, recover process will be triggered later ...")
        else:
            #time frame validation
            cond2_output = anchor2_res.stdout.split(r"\n")
            cond2_pattern = 'Adding consumer cancellation callback'
            cond2_time_stamp = fetch_timestamp_from_log(cond2_output,cond2_pattern)

            cond2_times = []
            for time_stamp in cond2_time_stamp:
                if time_compare(now,time_stamp,consumer_valid_time_range):
                    cond2_times.append(time_stamp)

            if len(cond2_times) == 0:
                logging.warning("The time stamp of anchor 2 is out of range - 60mins, we can skip now ...")
                return

            for declare_time in callback_error_times:
                for adding_time in cond2_times:
                    if time_compare(adding_time,declare_time,0):
                        logging.error("anchor #2 is earlier than anchor #1, not a useful anchor #2, will break now ...")
                        break
                    if not time_compare(adding_time,declare_time,2*60):
                        logging.error("anchor #2 is too far from anchor #1, need pay more attention on it ...")

            #check if cond 1 and cond 2 are good cases, otherwise regarding all the others the failure cases.
            # condition1 - empty after anchor 2
            try:
                cond1_cmd = "tail -50 " + callback_log_path + " | grep 'Adding consumer cancellation callback' -A 40 | wc -l"
                cond1_res = run(cond1_cmd)
            except Exception as cond1_err:
                logging.error("Call back consumer condition 1 check not met ! - %s",cond1_err)
                return

            if int(cond1_res.stdout) == 1:
                logging.info("Condition1 is met after anchor #2, callback service is in right working state, no need to do anything !")
                return

                # condition2 - right stuff followed after anchor 2
            log_callback_comsumer_cmd_res = None
            try:
                log_callback_comsumer_cmd_res = run(log_callback_comsumer_cmd)
            except Exception as e:
                logging.error("condition2 is not found after anchor #2, recover process will be triggered later ...!")
            else:
                # check again the successful of SENDING POST Request
                if log_callback_comsumer_cmd_res is not None and "{'result':'success'}" in log_callback_comsumer_cmd_res.stdout:
                    logging.info("Condition2 is met after anchor #2, callback service is in right working state, no need to do anything !")
                    return


    # 3) Get the key words for publisher side to confirm it's working right in latest 10 mins
    # [2021-04-26 20:22:38,519] [WARNING] - rmq_channel-send_msg- 132  : Publish could not be confirmed
    # [2021-04-26 20:40:41,299] [ERROR] - rmq_channel-send_msg- 124  : Pika exception
    # if both of them appear in the log, and the time stamp is mapping the log of above step 2),
    # Then we can say the callback service is in problem, we need do something now.
    #log_callback_publisher_cmd = "tail -50 /var/log/ATE/celery/callback_in_exec.log | grep 'Publish could not be confirmed'"
    # try:
    #     res3 = run(log_callback_publisher_cmd)
    # except Exception as e:
    #     logging.error("Received excpetion to run command to get the log of callback publisher for ATE %s, [%s]",current_host,e)
    #     exit()
    #
    # if res3:
    #     if res3.stderr:
    #         logging.error("Command to check publisher call back is failing with error %s" %res.stderr)
    #     if res3.stdout:
    #         # start to check callback_in_exec.log and see if error happening in last 10 mins
    #         output3 = res3.stdout.split(r"\n") # becareful here
    #         pattern3 = 'Publish could not be confirmed' # if find this pattern meaning that call back publisher has issue
    #         time_stamp3 = parse_callback_publisher_log(output3,pattern3)
    #         if not time_stamp3:
    #             logging.info("No error detected in callback.err for pattern %s" %(pattern3))
    #             exit()
    #         publisher_time_threshold = 10*60 # 10 mins
    #         now = datetime.datetime.utcnow()
    #         find_issue = False
    #         for time_stamp in time_stamp3:
    #             if time_compare(now,time_stamp3,publisher_time_threshold):
    #                 find_issue = True
    #                 break
    #         if not find_issue:
    #             is_publisher_ok = True



    #4)Try to do something on callback service
    logging.info("The log shows the exception for callback service, we need to recover it now ...")
    callback_recover(is_callback_queue_ok)



# === RMQ Service recovery part ===========================================================================================
'''
If we can't see myself in running nodes list, we can do service restart simply
Get the status of cluster
#Running Nodes
#
#rabbit@ant24ate01
#rabbit@ant24ate02
#rabbit@ant24ate03
'''
#==========================================================================================================================

def recover_rmq_service(self_key=''):
    rmq_cluster_status = "rabbitmqctl cluster_status | grep r'Running Nodes' -A 5"
    rmq_restart = "systemctl restart rabbitmq-server"

    try:
        rmq_status_res = run(rmq_cluster_status)
    except Exception as e:
        logging.error("Can't get RMQ cluster status from ATE %s - [%s], will skip this recovery process now ...",current_host,e)
        return

    rmq_status = rmq_status_res.stdout
    result = re.findall(r"ate\d{2}",rmq_status)
    if self_key in result:
        #['ate01', 'ate02', 'ate03']
        logging.info("Local RMQ instance is in cluster now,No need to do any recovery action on it, will skip it now ...")
    else:
        try:
            run(rmq_restart)
        except Exception as e:
            logging.error("Received exception %s to restart local RMQ, will exit now, need manual intervention for whole system...",e)


# output from ANT24 ant24ate02.ttve.mobilephone.net
current_host = socket.gethostname()
self_key = ''
if "ate" not in current_host:
    logging.error("Not in correct ATE VM, VM now is %s",current_host)
    exit()
else:
    res = re.search(r"ate\d+",current_host)
    if res is not None:
        self_key = res.group()


cf = configparser.ConfigParser()
try:
    cf.read("/etc/ATE/ATE.conf")
except Exception as e:
    logging.error( 'Exception occurred while opening ATE configuration file, will exit the recovery process now ... -: %s',e)
    exit()

is_recovery_enabled = False
try:
    is_recovery_enabled = cf.get('app','is_auto_recovery')
    is_recovery_enabled = True if is_recovery_enabled == "True" or is_recovery_enabled == "true" or is_recovery_enabled == "TRUE" else False
except Exception as exec:
    logging.error("Error encountered while fetching is_auto_recovery from config file, will exit the recovery process now ... -: %s",exec)

if is_recovery_enabled:
    recover_celery_service()
    recover_callback_service()
    recover_rmq_service(self_key)
else:
    logging.error("Recovery function is disabled now, will not trigger it ...")