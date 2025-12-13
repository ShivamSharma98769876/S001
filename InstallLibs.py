from kiteconnect import KiteConnect
import sys
print(sys.argv)


#api_key = "n683nqe7f3l7nzxl"
#api_secret = "11krc3ysc604ppxsvq60862pnq73t4qi"
#request_token = "3Ug8fbxP8PVLmHxJ8CNOVpikLGmy1HVT"  # Obtain this after login


api_key = "14vxzgvarfrfxs5k"
api_secret = "6wiefl80trb7t8psih5badkwlpijo1gd"

request_token = "UFOyn9cS0qctZPvW2RSJo0Egq7NjmeoU"  # Obtain this after login



#api_key = "ua8qzn6nt7kklv8z"
#api_secret = "2w2pcrxoa77dpc5z91vgkr91fmheeoh5"
#request_token = "GxLnTYQRDOA0TInfpLzX9H3E0hqKFo6P"  # Obtain this after login



#   4TNv7ByTFu2wlgDE2BZDXiXJRqo3jmwU

#   jHGSsQAf7fE83HeWtmQt5eT4XPBWXh7W

kite = KiteConnect(api_key=api_key)

# Generate session and get access token
try:
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data["access_token"]
    print("Access Token: ", access_token)

except Exception as e:
    print("Error generating access token: ", e)

