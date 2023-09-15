# Allowed Modules
import logging
import socket
import sys
import gzip
import ssl
# End of Allowed Modules
# Adding any extra module will result into score of 0

def retrieve_url(url):
    """
    return bytes of the body of the document at url
    """

    # Creating client socket to connect to host
    # using IPv4 and TCP protocol
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Checking if url is http or https to determine port
    if url.startswith("http://"):
        url = url[len("http://"):]
        port = 80
    elif url.startswith("https://"):
        client = ssl.wrap_socket(client)
        url = url[len("https://"):]
        port = 443
    else:
        return None

    # Extracting host and path from url
    if url.find("/") != -1:
        url = url.split("/", 1)
        host_and_port = url[0]
        path = url[1]
    else:
        host_and_port = url
        path = ""
        

    # Extracting host and port
    if host_and_port.find(":") != -1:
        host_and_port = host_and_port.split(":", 1)
        host = host_and_port[0]
        port = int(host_and_port[1])
    else:
        host = host_and_port
        
        # Converting emoji to readable domain
        host = host.encode('idna')
        
    try: 
        # connecting client to server
        client.connect((host, port))
        # Sending request to server
        request = f"GET /{path} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
        client.send(request.encode())
        response = b""
        response_splits = b""
        headers = b""
        body = b""
        final_response = b""
        while True:
            #  receiving response from server
            data = client.recv(4096)
            if not data:
                break
            response += data
            # Splitting header and body
            response_splits = response.split(sep=b'\r\n\r\n')
            headers = response_splits[0]
            body = response_splits[1]

            # checking if 200 ok
            if b'200 OK' not in headers:
                return None
            for line in headers.split(b'\r\n'):
                # checking for content length in header
                if b'Content-Length: ' in line:
                    content_length =  int(line[len('Content-Length: '):])
                    final_response += body
                    #  receiving data until the data is equal to its content length specified in header
                    while len(final_response) != content_length:
                        remaining_data = content_length - len(final_response)
                        final_response += client.recv(remaining_data) 
                # checking fortransfer-encoding in header
                elif b'Transfer-Encoding: chunked' in line:
                    content_length,_,body_content = body.partition(b'\r\n')
                    content_length = int(content_length, 16)
                    #  receiving data until the data is equal to its content length specified before the chunk
                    while content_length != 0:                        
                        final_response += body_content[:content_length]
                        body = client.recv(4096)
                        content_length,_,body_content = body.partition(b'\r\n')
                        content_length = int(content_length, 16)
            # for persistant connections
            if b'100 Continue' in headers:
                continue
            
            client.close()
            # print(final_response)
            return final_response

    except socket.error as exc:
        return None

    # return b"this is unlikely to be correct"

if __name__ == "__main__":
    sys.stdout.buffer.write(retrieve_url(sys.argv[1]))
