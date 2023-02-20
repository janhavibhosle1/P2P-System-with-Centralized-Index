import socket
import threading

server=('', 7734)
serverSock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    serverSock.bind(server)
    serverSock.listen(5)
    print("Started listening on Port", 7734)
except socket.error:
    print("Port already in use")
    raise SystemExit

clientList={} # To maintain ClientName and PortNumber associated
rfcList={} # To maintain RFC List and Clientnames as Key-Value
rfcTitle={} #To maintain RFC Number and Title as Key-Value
flag=True

def addResponse(rfcNum,rfcTitle,clientName,clientPort):
    addMessage="P2P-CI/1.0 200 OK\n"\
                "RFC "+str(rfcNum)+" "+rfcTitle+" "+clientName+" "+clientPort+"\n"
    return addMessage

def lookupResponse(rfcNum):
    if rfcNum in rfcList:
        lookupMessage="P2P-CI/1.0 200 OK\n"
        for clientName in rfcList[int(rfcNum)]:
            lookupMessage+="RFC "+str(rfcNum)+" "+rfcTitle[rfcNum]+" "+clientName+" "+clientList[clientName]+"\n"
    else:
        lookupMessage="P2P-CI/1.0 404 Not Found\n"
    return lookupMessage

def listResponse():
    listMessage="P2P-CI/1.0 200 OK\n"
    for rfcNum,Title in rfcTitle.items():
        for clientName in rfcList[rfcNum]:
            listMessage+="RFC "+str(rfcNum)+" "+Title+" "+clientName+" "+clientList[clientName]+"\n"
    return listMessage

def p2sAdd(req):
    data=""
    for method in req:
        split_req=list(method.split("\n"))
        if "P2P-CI/1.0" not in split_req[0]:
            data="P2P-CI/1.0 505 Version Not Supported\n"
        else:
            _,_,rfcNum,_=split_req[0].split(" ")
            _,client=split_req[1].split(" ")
            _,clientPort=split_req[2].split(" ")
            _,Title=split_req[3].split(" ")
            if int(rfcNum) in rfcTitle and client not in rfcList[int(rfcNum)]:
                if rfcTitle[int(rfcNum)]==Title:
                    rfcList[int(rfcNum)].append(client)
                    data+=addResponse(rfcNum,Title,client,clientPort)
                else:
                    data="P2P-CI/1.0 400 Bad Request\n"
            elif int(rfcNum) in rfcTitle and client in rfcList[int(rfcNum)]:
                data+=addResponse(rfcNum,Title,client,clientPort)
            else:
                rfcTitle[int(rfcNum)]=Title
                rfcList[int(rfcNum)]=[client]
                data+=addResponse(rfcNum,Title,client,clientPort)
    return data

def p2sList(req):
    split_req=list(req[0].split("\n"))
    if "P2P-CI/1.0" not in split_req[0]:
        data="P2P-CI/1.0 505 Version Not Supported\n"
    else:
        data=listResponse()
    return data

def p2sLookup(req):
    split_req=list(req[0].split("\n"))
    _,_,rfcnum,_=split_req[0].split(" ")
    _,title=split_req[3].split(" ")
    if not rfcnum.isnumeric() or int(rfcnum) not in rfcTitle:
        data="P2P-CI/1.0 400 Bad Request\n"
    elif "P2P-CI/1.0" not in split_req[0]:
        data="P2P-CI/1.0 505 Version Not Supported\n"
    elif rfcTitle[int(rfcnum)]==title:
        data=lookupResponse(int(rfcnum))
    else:
        data="P2P-CI/1.0 400 Bad Request\n"
    return data

def deleteClient(clientName):
    rfc_tmp=[]
    for rfc in rfcList.keys():
        if clientName in rfcList[rfc]:
            rfcList[rfc].remove(clientName)
        if len(rfcList[rfc])==0:
            rfc_tmp.append(rfc)
    for rfc in rfc_tmp:
        del rfcList[rfc]
        del rfcTitle[rfc]
    del clientList[clientName]
    print(clientName+" has been deleted from the list")

def p2sRequest(conn):
    while True:
        request=conn.recv(1024)
        request=request.decode('utf-8')
        print("Message Received\n",request)           
        req=request.split("\n\n")
        if "\n\n" in request:
            del req[-1]
        split_req=list(req[0].split("\n"))
        _,client=split_req[1].split(" ")
        if client not in clientList:
            _,clientPort=split_req[2].split(" ")
            clientList[client]=clientPort
            print(client+" has been added to the list")
        if 'ADD' in request:
            data=p2sAdd(req)
            conn.sendall(data.encode('utf-8'))
        if "LIST" in request:
            data=p2sList(req)
            conn.sendall(data.encode('utf-8'))
        if "LOOKUP" in request:
            data=p2sLookup(req)
            conn.sendall(data.encode('utf-8'))
        if "DISCONNECT" in request:
            print("DISCONNECT message received from the "+client+" Closing connection of the client "+client)
            deleteClient(client)
            break
try:
    while True:
        conn, addr = serverSock.accept()
        print("Received connection from", addr)
        serverThread=threading.Thread(target=p2sRequest, args=(conn,))
        serverThread.start()
except KeyboardInterrupt:
    flag=False
    serverSock.close()
    print("Stopping the server\n")
    raise SystemExit