"""
This file implements a system that combine all current query into one larger request and send to lua server

This is to reduce the frequency of socket activity

All request will use only one loop
each type of request will use only one
"""
