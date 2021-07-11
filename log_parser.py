import datetime
import readlog

output = 'INFO       2021-05-06 22:06:11,059 __main__        post_send             367 : Sending post request for message # 7647\nINFO       2021-05-06 22:06:11,066 __main__        post_send             367 : Sending post request for message # 7648\nINFO       2021-05-06 22:06:11,072 __main__        post_send             367 : Sending post request for message # 7649\nINFO       2021-05-06 22:06:11,079 __main__        post_send             367 : Sending post request for message # 7650\nINFO       2021-05-06 22:06:11,263 __main__        post_send             367 : Sending post request for message # 7651\nINFO       2021-05-06 22:06:11,815 __main__        post_send             367 : Sending post request for message # 7652\nINFO       2021-05-06 22:06:11,857 __main__        post_send             367 : Sending post request for message # 7653\nINFO       2021-05-06 22:06:11,866 __main__        post_send             367 : Sending post request for message # 7654\nINFO       2021-05-06 22:06:42,751 __main__        post_send             367 : Sending post request for message # 7655\nINFO       2021-05-06 22:07:01,669 __main__        post_send             367 : Sending post request for message # 7656\nINFO       2021-05-06 22:07:33,293 __main__        post_send             367 : Sending post request for message # 7657\nINFO       2021-05-06 22:07:36,738 __main__        post_send             367 : Sending post request for message # 7658\nINFO       2021-05-06 22:10:18,700 __main__        post_send             367 : Sending post request for message # 7659\n'
output = output.split("\n")
# print(output)

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

# now = datetime.datetime.utcnow()
# print(now)
# time_list = parse_callback_err_log(output,"Sending post request for message")
# diff = now - time_list[0]
# print(diff.seconds)

output = r"[2021-05-01 07:15:02,815] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-01 07:15:03,139] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-01 07:15:03,431] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-01 07:15:03,909] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-01 07:15:04,201] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-01 07:15:04,352] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-01 23:27:58,947] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-02 00:06:20,366] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-02 23:15:01,819] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-02 23:52:28,063] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 00:31:09,353] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 22:40:31,502] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 22:52:54,930] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 23:10:07,534] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 23:21:45,848] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 23:31:19,783] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 23:38:55,379] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 23:41:17,817] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-03 23:55:11,429] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-04 00:12:53,743] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-04 23:29:12,084] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-05 17:36:13,336] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-05 17:52:28,161] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-05 21:26:59,165] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n[2021-05-06 22:00:01,781] [WARNING] - rmq_channel-fetch_app- 70   : Fetch Config Data Warning -- No option 'rabbitmq_timeout' in section: 'app', default value will be used\n"

pattern = "Fetch Config Data Warning" #'Publish could not be confirmed'
output = output.split(r"\n")

#print(len(output))

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

print(parse_callback_publisher_log(output,pattern))