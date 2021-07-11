import re
from collections import Counter,defaultdict



def file_open(file_name):
    # return a log object that can be parsed later
    with open(file_name,"r") as f:
        log = f.read()
    if log:
        return log


def log_parse(log_file):
    if log_file:
        ip_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        ip_lists = re.findall(ip_pattern,log_file)
        response_pattern = r"\s\d{3}\s"
        response_lists = re.findall(response_pattern,log_file)
        #request_pattern = r'\s\"[A-Z].+\d\"\s'
        request_pattern = r"\"(.+?)\" \d{3}"
        request_lists = re.findall(request_pattern,log_file)
        return ip_lists,response_lists,request_lists
    return "none can be found!"


def log_parser(log_file):
    pattern = r'([(\d\.)]+) - - \[(.*?)\] "(.*?)" (\d+) - "(.*?)" "(.*?)"'
    response = re.match(pattern,log_file)
    return response

if __name__ == "__main__":
    logs = file_open("apache.log")
    ips, resps, reqs = log_parse(logs)
    #print(logs)
    # print(Counter(resps))
    # print(len(reqs))
    err_cnt,req_method_dict = 0, defaultdict(int)
    for req in reqs:
        if "GET" in req:
            req_method_dict["GET"] += 1

    # print(req_method_dict)
    #print(reqs,type(reqs),len(reqs))
    string = '180.76.6.56 - - [20/May/2015:21:05:56 +0000] "GET /robots.txt HTTP/1.1" 200 - "-" "Mozilla/5.0 (Windows NT 5.1; rv:6.0.2) Gecko/20100101 Firefox/6.0.2" '
    print(log_parser(string).groups())
    #print(ips, len(ips))

