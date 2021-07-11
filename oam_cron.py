'''
Created on Apr 30, 2021

@author: xt153g
'''
from invoke import run
import logging,readlog,socket
import datetime


def time_compare(cur_time,prev_time,time_threshold):
    # function to compare the timestamp to make sure cur_time - prev_time <= time_threshold
    # return type Bool
    # use datetime pbj and datetime delta obj
    if (cur_time - prev_time).seconds <= time_threshold:
        return True
    return False


def parse_callback_err_log(output,pattern):
    # if pattern existing in output , return its timestamp
    #pattern = "Sending post request for message"
    timestamps = []
    temp = []
    for op in output:
        if pattern in op:
            # 2021-05-06 22:06:11 UTC
            timestamp = readlog.search(r"\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}", op)
            if timestamp:
                temp.append(timestamp.group())

    if temp:
        for timestamp in temp:
            # convert all time stamp from string to UTC time
            date_time_obj = datetime.datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S")
            timestamps.append(date_time_obj)

    return timestamps

def parse_callback_publisher_log(output,pattern):
    # if pattern existing in output , return its timestamp
    #pattern = "Sending post request for message"
    timestamps = []
    temp = []
    for op in output:
        if pattern in op:
            # 2021-05-06 22:06:11 UTC
            timestamp = readlog.search(r"\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}", op)
            if timestamp:
                temp.append(timestamp.group())
    #print(temp)
    if temp:
        for timestamp in temp:
            # convert all time stamp from string to UTC time
            date_time_obj = datetime.datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S")
            timestamps.append(date_time_obj)

    return timestamps

# output from ANT24 ant24ate02.ttve.mobilephone.net
current_host = socket.gethostname()
if "ate" not in current_host:
    logging.error("Not in correct ATE VM, VM now is %s",current_host)
    exit()

# === Celery Service hung recovery part =============================================================================
rmq_queue_cmd = "rabbitmqctl list_queues -p celery | grep priority_high_long"
log_celery_cmd = "tail -50 /var/log/ATE/celery/celeryd.err | grep 'missed heartbeat'"
task_num = 0

# check if has privilege to run the command
has_privilege = run(rmq_queue_cmd+"|wc -l")
if not has_privilege:
    logging.error("Script does not have privilege to run command.")
    exit()

try:
    res = run(rmq_queue_cmd)
except Exception as e:
    logging.error("Received exception to run command to get the tasks number in queue priority_high_long, [%s]",e)
    exit()

if not res.stderr and res.stdout is not None:
    task_num = readlog.split('\t|\n', res.stdout)[1]  #['priority_high_long', '0', '']


try:
    res = run(log_celery_cmd)

except Exception as e:
    # if exception happens, means log_celery_cmd did not find anything. mostly the celery is working fine.
    logging.error("Received excpetion to run command to get the log of celery for ATE %s, [%s]",current_host,e)
    exit()

if res.stdout is not None and int(task_num) > 0:
    logging.error("%s tasks queued and encountered the missed heartbeat scenario recently, will restart celery service to fix the hung workers")
    action_cmd = "/ENV2.7/bin/supervisorctl -c /etc/supervisord.worker restart celery"
    try:
        res = run(action_cmd)
        if "celery: started" not in res.stdout:
            logging.error("Celery restart not successful,please manually check.")
            exit()
    except Exception as e:
        logging.error("Received exception when restart the celery service - [%s]",e)
        exit()
else:
    logging.warn("queued task is %s and log result is [%s]",task_num,res.stdout) # res is log_celery_cmd




# === Callback Service recovery part =================================================================================
'''
res1,res2,res3,res4,res5
'''
res1,res2,res3,res4,res5=None,None,None,None,None
rmq_callback_queue = "rabbitmqctl list_queues -p celery | grep callback_queue"
log_callback_comsumer_cmd = "tail -50 /var/log/ATE/callback/callback.err | grep 'Sending post request' -B 5 -A 5"
log_callback_publisher_cmd = "tail -50 /var/log/ATE/celery/callback_in_exec.log | grep 'Publish could not be confirmed'"
rebuild_callback_queue = "rabbitmqctl eval 'Q = {resource, <<\"celery\">>, queue, <<\"callback_queue\">>}, rabbit_amqqueue:internal_delete(Q, <<\"CLI\">>).'"
restart_callback = "/ENV2.7/bin/supervisorctl -c /etc/supervisord.web restart callback"
is_callback_queue_ok = False
is_consumer_ok = False
is_publisher_ok = False
is_callback_ok = False

# 1) Get the result that if this queue is there
# callback_queue    0
# 'callback_queue\t0\n
try:
    res1 = run(rmq_callback_queue)
except Exception as e:
    logging.error("Received excpetion to run command to get callback queue status for ATE %s - [%s], RMQ must be out of service, will exit now...",current_host,e)
    exit()
if res1:
    if res.stdout and "callback_queue" in res.stdout:
        logging.info("Callback queue is running correctly, reserving it for next checking step...")
        is_callback_queue_ok = True


# 2) Analyzing the key words to confirm if it's not working right in latest half hour.
# INFO       2021-04-27 16:42:59,682 __main__        setup_queue           204 : Declaring queue callback_queue
# ...
# is it : INFO       2021-04-27 16:43:41,119 __main__        add_on_cancel_callback  257 : Adding consumer cancellation callback
# or not above correct subsequent log
try:
    cmd = "tail -50 /var/log/ATE/callback/callback.err | grep 'Declaring queue callback_queue'"
    res2 = run(cmd)
except Exception as e:
    # the consumer queue is fine because patter 'Declaring queue callback_queue' is not existing.
    logging.error("Received excpetion to run command to get the log of callback consumer service for ATE %s, [%s]",current_host,e)
    exit()
if res2:
    if res2.stderr:
        logging.error("Command to check consumer call back is failing for ATE %s, failure reason is %s" %(current_host, res2.stderr))
    if res2.stdout:
        # start to parsing log. Check if the error is happening in last 30 mins ( not 1hour ago, not yesterday , not 2days ago)

        output = res2.stdout.split(r"\n")
        pattern2 = 'Declaring queue callback_queue'
        time_stamp2 = parse_callback_err_log(output,pattern2)
        if not time_stamp2:
            logging.info("No error detected in callback.err for pattern %s" %(pattern2))
            exit()
        consumer_time_threshold = 30*60 # 30 mins
        now = datetime.datetime.utcnow()

        callback_error_times = []
        for time_stamp in time_stamp2:
            if time_compare(now,time_stamp,consumer_time_threshold):
                callback_error_times.append(time_stamp)

        if len(callback_error_times) == 0:
            logging.warning("No call back error time is available")
            exit()

        # since we suspect there is call back error now .  check below conditions
        # conditon1 : empty lines after 'Declaring queue callback_queue'  --- working
        # condition2: 'Adding consumer cancellation callback' existing and shows up within 2min of time that 'Declaring queue callback_queue' show up
        # all other condition is considered as callback_queue NOT OK.  is_consumer_ok = False

        # condition1
        is_cond1_ok,is_cond2_ok = False,False
        try:
            cond1_cmd = "tail -50 /var/log/ATE/callback/callback.err | grep 'Declaring queue callback_queue' -A 40 | wc -l"
            cond1_res = run(cond1_cmd)
        except Exception as cond1_err:
            logging.error("Call back consumer condition 1 check not met !")
            exit()

        if int(cond1_res.stdout) == 0:
            is_cond1_ok = True

        # condition2
        try:
            cond2_cmd = "tail -50 /var/log/ATE/callback/callback.err | grep 'Adding consumer cancellation callback' "
            cond2_res = run(cond2_cmd)
        except Exception as cond1_err:
            logging.error("Call back consumer condition 2 check not met !")
            exit()

        cond2_output = cond2_res.stdout.split(r"\n")
        cond2_pattern = 'Adding consumer cancellation callback'
        cond2_time_stamp = parse_callback_err_log(cond2_output,cond2_pattern)
        if not cond2_time_stamp:
            logging.info("No error detected in callback.err for pattern %s" %(cond2_pattern))
            exit()
        #cond2_consumer_time_threshold = 30*60 # 30 mins
        cond2_times = []
        for time_stamp in cond2_times:
            if time_compare(now,time_stamp,consumer_time_threshold):
                #callback_error_times.append(time_stamp)
                cond2_times.append(time_stamp)

        if len(cond2_times) == 0:
            logging.warning("No call back error time is available for condition2")
            exit()
        # callback_error_times  -- save time for 'Declaring queue callback_queue'
        # cond2_times            -- save time for  'Adding consumer cancellation callback'

        for declare_time in callback_error_times:
            for adding_time in cond2_times:
                if time_compare(declare_time,adding_time,2*60):
                    is_cond2_ok = True
                    break
            if is_cond2_ok :
                break

        if is_cond1_ok or is_cond2_ok:
            is_consumer_ok = True
            logging.info("call back consumer queue is working. no need to restart queue!")



# 3) Get the key words to confirm it's working right in latest 10 mins
# [2021-04-26 20:22:38,519] [WARNING] - rmq_channel-send_msg- 132  : Publish could not be confirmed
# [2021-04-26 20:40:41,299] [ERROR] - rmq_channel-send_msg- 124  : Pika exception
# if both of them appear in the log, and the time stamp is mapping the log of above step 2),
# Then we can say the callback service is in problem, we need do something now.
#log_callback_publisher_cmd = "tail -50 /var/log/ATE/celery/callback_in_exec.log | grep 'Publish could not be confirmed'"
try:
    res3 = run(log_callback_publisher_cmd)
except Exception as e:
    logging.error("Received excpetion to run command to get the log of callback publisher for ATE %s, [%s]",current_host,e)
    exit()

if res3:
    if res3.stderr:
        logging.error("Command to check publisher call back is failing with error %s" %res.stderr)
    if res3.stdout:
        # start to check callback_in_exec.log and see if error happening in last 10 mins
        output3 = res3.stdout.split(r"\n") # becareful here
        pattern3 = 'Publish could not be confirmed' # if find this pattern meaning that call back publisher has issue
        time_stamp3 = parse_callback_publisher_log(output3,pattern3)
        if not time_stamp3:
            logging.info("No error detected in callback.err for pattern %s" %(pattern3))
            exit()
        publisher_time_threshold = 10*60 # 10 mins
        now = datetime.datetime.utcnow()
        find_issue = False
        for time_stamp in time_stamp3:
            if time_compare(now,time_stamp3,publisher_time_threshold):
                find_issue = True
                break
        if not find_issue:
            is_publisher_ok = True

"""
Add by Yue
is_callback_queue_ok = False
is_consumer_ok = False
is_publisher_ok = False
if all above command are True , meaning is_call_back_ok = True
"""
if is_callback_queue_ok and is_consumer_ok and is_publisher_ok:
    is_callback_ok = True
    logging.info("Call back all ok. no need to restart anything.")
    exit()

# Try to do something on callback service
# if queue is running, just restart this service
# else do step 1) restart service; step 2) rebuild the queue in RMQ
if not is_callback_ok:
    try:
        res4 = run(restart_callback)
    except Exception as e:
        logging.error("Received excpetion to run command to get the log of callback consumer service for ATE %s, [%s]",current_host,e)
        exit()
    if "callback: started" not in res4.stdout:
        logging.error("call back service can not be restarted during recover process.")
        exit()

    # check the callback service restarted successfully or not from callback.err
    # time.sleep(2min) ?
    # just need to search if patter "Adding consumer cancellation callback" showing in last 1 min or not
    try:
        callback_recover_res = run("tail -50 /var/log/ATE/callback/callback.err | grep 'Adding consumer cancellation callback'")
    except Exception as e:
        logging.error("callback recover searching for 'adding consumer call back' is failing'")
        exit()

    callback_recovered_pattern = "Adding consumer cancellation callback"

    callback_recovered_time = parse_callback_err_log(callback_recover_res.stdout,callback_recovered_pattern)

    callback_recover_now = datetime.datetime.utcnow()

    if len(callback_recovered_time) == 0:
        logging.error("No timestamp is available for callback_recovered_pattern ,exit now!")
        exit()

    for tm in callback_recovered_time:
        if time_compare(callback_recover_now,tm,1*60):
            is_callback_queue_ok = True
            break

    if not is_callback_queue_ok: # callback_queue not recovered by restarting callback service. Rebuild the queue.
        try:
            res5 = run(rebuild_callback_queue)
        except Exception as e:
            logging.error("Received excpetion to run command to get the log of callback consumer service for ATE %s, [%s]",current_host,e)
            exit()


# === RMQ Service recovery part ===========================================================================================
rmq_cluster_status = "rabbitmqctl cluster_status | grep r'Running Nodes' -A 5"
rmq_restart = "systemctl restart rabbitmq-server"

# Get the status of cluster
#Running Nodes
#
#rabbit@ant24ate01
#rabbit@ant24ate02
#rabbit@ant24ate03
# If the one match the local in not there, restart myself.
try:
    rmq_status_res = run(rmq_cluster_status)
except Exception as e:
    logging.error("Received excpetion to run command to get RMQ cluster status for ATE %s - [%s], will restart RMQ service locally...",current_host,e)
    rmq_status = rmq_status_res.stdout
    if len(readlog.findall(r"ate\d{2}", rmq_status)) == 3:
        #['ate01', 'ate02', 'ate03']
        logging.info("RMQ status are good after rebuild,everything is done to fix issue!")
    else:

        try:
            rmq_restart_res = run(rmq_restart)
        except Exception as e:
            logging.error("Received exception to restart local RMQ, will exit now, need manual intervetion for whole system...")
        exit()

#cluster_output = res.stdout
