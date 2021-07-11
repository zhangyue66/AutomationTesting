import re

string = '180.76.6.56 - - [20/May/2015:21:05:56 +0000] "GET /robots.txt HTTP/1.1" 200 - "-" "Mozilla/5.0 (Windows NT ' \
         '5.1; rv:6.0.2) Gecko/20100101 Firefox/6.0.2" '
string1 = '46.105.14.53 - - [20/May/2015:21:05:15 +0000] "GET /blog/tags/puppet?flav=rss20 HTTP/1.1" 200 14872 "-" \
            "UniversalFeedParser/4.2-pre-314-svn +http://feedparser.org/"'
pattern = r'\s"[A-Z].+\d"\s'
yz = re.findall(pattern,string1)
print(len(yz))
print(yz)
yz = re.findall(pattern,string)
print(len(yz))
print(yz)
#print(string.split(" "))



hostname = "ant24ate01"
p = r"(ate\d+)"
res = re.search(p,hostname)
print(res.group())


digits = "     -42   "
p1 = r"[-+]?\d+"
res1 = re.search(p1,digits)
if res1:
    print(res1.group())

s,t = "agg","efk"
yz = zip(s,t)
print(list(yz))


li = [(1,2),(3,4)]
import heapq
heapq.heapify(li)
print(li[0])
print(list(li))
small = heapq.heappop(li)
print(small)

set1 = set()
set1.add(1)
set1.add(2)

heapq.heapify(list(set1))


products = ["mobile","mouse","moneypot","monitor","mousepad"]
products.sort()
print(products)

yz = [1,2,3,4]
def func(n):
    return n*n
for num in map(func,yz):
    print(num)

kk = \
"""
abc
"""
print(kk)

events = [[47,50],[33,41],[39,45],[33,42],[25,32],[26,35],[19,25],[3,8]]
events.sort()
print(events)

pass_heap = [(1, 2, 3), (2, 3, 4), (3, 4, 5), (0, 77, 88)]
heapq.heapify(pass_heap)
print(pass_heap)


A = [1, 2, 5, 7, 8, 12]

def binary_search(nums,target):
    l,r = 0,len(nums)-1
    while l <= r:
        mid = l + (r-l)//2
        if nums[mid] == target:
            return mid
        if nums[mid] > target:
            r = mid - 1
        else:
            l = mid + 1
    return -1


print(binary_search(A, 12))

def bin_sec_l(nums,target):
    # [l,r)
    l,r = 0,len(nums)
    while l < r:
        mid = l + (r-l)//2
        if nums[mid] == target:
            return mid
        if nums[mid] > target:
            r = mid
        else:
            l = mid + 1
    return -1


print(bin_sec_l(A, 1))

B = [1,2,3]
print(bin_sec_l(B,0))

arr = [4,5,8,10,12]
arr = [1,2,3,4,5]
arr = [0,0,1,2,3,3,4,7,7,8]
def bin_lower_bound(nums,target):
    l,r = 0,len(nums)
    while l < r :
        mid = l + (r-l)//2
        if nums[mid] >= target:
            r = mid
        else:
            l = mid+1
    return l
print(bin_lower_bound(arr,5))


