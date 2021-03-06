#!/usr/bin/python
from __future__ import print_function
from __future__ import absolute_import
__author__ = 'https://github.com/chelnak'
import json

import requests

from .helpers import authenticate, checkResponse
from prettytable import PrettyTable


class ConsumerClient(object):
    def __init__(self, host, username, password, token='', tenant=None):
        """
		Creates a connection to the vRA REST API using the provided
		username and password.
		Parameters:
	                host = vRA Appliance fqdn
        	        user = user account with access to the vRA portal
                	passowrd = valid password for above user
			token = auth token if already acquired via previous client
	                tenant = tenant for user. if this is NONE it will default to "vsphere.local"
		"""

        if tenant is None:
            tenant = "vsphere.local"

        self.host = host
        self.username = username
        self.password = password
        self.tenant = tenant
        if(token==''):
                self.token = authenticate(host, username, password, tenant)
        else:
                self.token = token

    def getToken(self):
        """
		Function that prints the bearer token for the session.
		This is only for troubleshooting.
		"""

        return self.token

    def getResource(self, id, show='json'):
        """
		Function that will get a vRA resource by id.
		Parameters:
            show = return data as a table or json object
			id = id of the vRA resource.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/resources/{id}'.format(host=host, id=id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        resource = r.json()

        if show == 'table':
            table = PrettyTable(['Id', 'Name', 'Status', 'Catalog Item'])
            table.add_row([
                resource['id'], resource['name'], resource['status'],
                resource['catalogItem']['label']
            ])

            print(table)

        elif show == 'json':
            return resource

    def getResourceByName(self, name, show='json'):
        """
        Function that will get a vRA resource by id.
        Parameters:
            show = return data as a table or json object
            name = name of the vRA resource.
        """

        host = self.host
        token = self.token

        url = "https://{host}/catalog-service/api/consumer/resources?$filter=name%20eq%20'{name}'".format(host=host, name=name)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        resource = r.json()

        if show == 'table':

            table = PrettyTable(['Id', 'Name', 'Status', 'Catalog Item'])
            table.add_row([
                resource['content'][0]['id'], resource['content'][0]['name'], resource['content'][0]['status'],
                        resource['content'][0]['catalogItem']['label']
                    ])

            print(table)

        elif show == 'json':
            return resource['content'][0]

    def getResourceByBusinessGroup(self, name, limit=100, show='json'):
        """
        Function that will get all vRA resources running
        for a specific Business group
        Parameters:
            show = return data as a table or json object
            name = name of the vRA resource.
        """

        host = self.host
        token = self.token

        url = "https://{host}/catalog-service/api/consumer/resources?$filter=organization/subTenant/name%20eq%20'{name}'&limit={limit}".format(host=host, name=name, limit=limit)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        resource = r.json()

        if show == 'table':

            table = PrettyTable(['Id', 'Name', 'Description','Label' 'Status'])
            for item in resource['content']:
                table.add_row([
                    item['id'], item['name'], item['description'],
                    item['resourceTypeRef']['label'], item['status'],
                    ])

            print(table)

        elif show == 'json':
            return resource

    def getResourceIdByName(self, name):
        return self.getResourceByName(name)["id"]

    def getResourceDataEntriesAsDict(self, id=None, resource=None):
        assert id or resource
        assert not id or not resource
        if resource is None:
            resource = self.getResource(id)
        resourceDataEntries = resource["resourceData"]["entries"]
        keys = set(entry["key"] for entry in resourceDataEntries)
        return {key: [entry.get("value") for entry in resourceDataEntries if entry["key"] == key] for key in keys}

    def getMachineStatus(self, id=None, resource=None):
        resourceDataDict = self.getResourceDataEntriesAsDict(id=id, resource=resource)
        machineStatus = resourceDataDict["MachineStatus"]
        assert len(machineStatus) == 1
        return machineStatus[0][u"value"]

    def getMachineIP(self, id=None, resource=None):
        resourceDataDict = self.getResourceDataEntriesAsDict(id=id, resource=resource)
        machineStatus = resourceDataDict["ip_address"]
        assert len(machineStatus) == 1
        return machineStatus[0][u"value"]

    def getResourceActions(self, id, raw=False):
        host = self.host
        token = self.token

        url = "https://{host}/catalog-service/api/consumer/resources/{id}/actions".format(host=host, id=id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        actions = r.json()
        if raw:
            return actions
        actionsContent = actions["content"]
        return {action["name"]: action for action in actionsContent}
        #keys = set(action["name"] for action in actionsContent)
        #return {key: [action for action in actionsContent if action["name"] == key] for key in keys}

    def getResourceIdByRequestId(self, id):
        """
		Function that will search for a resource with a matching requestId.
		Parameters:
			id = request id of the vRA resource.
		"""

        host = self.host
        token = self.token

        url = "https://{host}/catalog-service/api/consumer/resources?$filter=request%20eq%20'{id}'".format(host=host, id=id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        resource = r.json()
        resourceId = resource['content'][0]['id']

        return resourceId

    def getAllResources(self, show='table', limit=20):
        """
		Function that will return all resources that are available to the current user.
        Parameters:
            show = return data as a table or json object
        	limit = The number of entries per page.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/resources?limit={limit}&$orderby=name%20asc'.format(
            host=host, limit=limit)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        resources = r.json()

        if show == 'table':
            table = PrettyTable(['Id', 'Name'])

            for i in resources['content']:
                table.add_row([i['id'], i['name']])

            print(table)

        elif show == 'json':
            return resources['content']

    def getResourceNetworking(self, id=None, show='json', resource=None):
        """
		Function that will return networking information for a given resource.
		Parameters:
            show = return data as a table or json object
			id = id of the vRA resource.
		"""

        assert id or resource
        assert not id or not resource
        if resource is None:
            resource = self.getResource(id)

        resourceData = resource['resourceData']['entries']

        for i in resourceData:
            if i['key'] == 'NETWORK_LIST':
                networkList = i['value']['items']
                for j in networkList:
                    entries = j['values']['entries']

        if show == 'table':
            table = PrettyTable(['Component', 'Value'])

            for i in entries:
                table.add_row([i['key'], i['value']['value']])

            print(table)

        elif show == 'json':
            return entries

    def getResourceNetworkAddresses(self, id=None, resource=None):
        net = self.getResourceNetworking(id=id, resource=resource)
        return [x[u"value"][u"value"] for x in net if x[u"key"] == u"NETWORK_ADDRESS"]

    def getEntitledCatalogItems(self, show='table', limit=20):
        """
		Function that will return all entitled catalog items for the current user.
        Parameters:
            show = return data as a table or json object
    		limit = The number of entries per page.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/entitledCatalogItems?limit={limit}&$orderby=name%20asc'.format(
            host=host, limit=limit)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        items = r.json()

        if show == 'table':
            table = PrettyTable(['Id', 'Name'])

            for i in items['content']:
                table.add_row([i['catalogItem']['id'],
                               i['catalogItem']['name']])

            print(table)

        elif show == 'json':
            return items['content']

    def getEntitledCatalogItemsAsDict(self):
        content = self.getEntitledCatalogItems(show="json")
        items = [element["catalogItem"] for element in content]
        return {item["name"]: item for item in items}

    def getCatalogItemForm(self, catalogItem):
        host = self.host
        token = self.token
        url = 'https://{host}/catalog-service/api/consumer/catalogItems/{id}/forms/request'.format(host=host, id=catalogItem["id"])
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        form = r.json()
        return form

    def getCatalogItemTemplate(self, catalogItem):
        host = self.host
        token = self.token
        url = 'https://{host}/catalog-service/api/consumer/entitledCatalogItems/{id}/requests/template'.format(host=host, id=catalogItem["id"])
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        form = r.json()
        return form

    def getCatalogItemFormDetails(self, catalogItem):
        host = self.host
        token = self.token
        url = 'https://{host}/catalog-service/api/consumer/catalogItems/{id}/forms/details'.format(host=host, id=catalogItem["id"])
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        form = r.json()
        return form

    def getCatalogItemFormDetailsEntries(self, catalogItem):
        entries = self.getCatalogItemFormDetails(catalogItem)["values"]["entries"]
        keys = set(entry["key"] for entry in entries)
        return {key: [entry.get("value") for entry in entries if entry["key"] == key] for key in keys}

    def getRequest(self, id, show='table'):
        """
		Function that will return request information for a given request.
		Parameters:
			id = the id of the vRA request.
            show = return data as a table or json object
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/requests/{id}'.format(host=host, id=id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)

        request = r.json()

        if show == 'table':
            table = PrettyTable(['Id', 'Request Number', 'Item', 'State'])
            table.add_row([request['id'], request['requestNumber'], request['requestedItemName'], request['state']])

            print(table)

        elif show == 'json':
            return request

    def getAllRequests(self, show='table', limit=20):
        """
		Function that will return the resource that were provisioned as a result of a given request.

		Parameters:
                show = return data as a table or json object
			    limit = The number of entries per page.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/requests?limit={limit}&$orderby=requestNumber%20desc'.format(host=host, limit=limit)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)

        items = r.json()

        if show == 'table':
            table = PrettyTable(['Id', 'Request Number', 'Item', 'State'])

            for i in items['content']:
                table.add_row([i['id'], i['requestNumber'], i['requestedItemName'], i['state']])

            print(table)

        elif show == 'json':
            return items['content']

    def getRequestResource(self, id):
        """
		Function that will return the resource that were provisioned as a result of a given request.
		Parameters:
			id = the id of the vRA request.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/requests/{id}/resources'.format(host=host, id=id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)

        resource = r.json()

        return resource['content']

    def requestResource(self, payload):
        """
		Function that will submit a request based on payload.
		payload = json body (example in request.json)
		Parameters:
			payload = JSON request body.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/requests'.format(host=host)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.post(url=url,
                          data=payload,
                          headers=headers,
                          verify=False)
        checkResponse(r)

        id = r.headers['location'].split('/')[7]

        return id

    def requestMachine(self, catalog_id, payload):
        """
		Function that will submit a request based on payload.
		payload = json body (example in request.json)
		Parameters:
			payload = JSON request body.
		"""

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/entitledCatalogItems/{id}/requests'.format(host=host, id=catalog_id)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.post(url=url,
                          data=payload,
                          headers=headers,
                          verify=False)
        checkResponse(r)

        id = r.headers['location'].split('/')[7]

        return id

    def performAction(self, resource, actionID=None, requestDataEntries=None):

        host = self.host
        token = self.token

        url = 'https://{host}/catalog-service/api/consumer/resources/{id}/actions/{actionID}/requests/template'.format(host=host, id=resource['id'], actionID=actionID)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': token
        }
        r = requests.get(url=url, headers=headers, verify=False)
        checkResponse(r)
        template = r.json()

        url = 'https://{host}/catalog-service/api/consumer/resources/{id}/actions/{actionID}/requests'.format(host=host, id=resource['id'], actionID=actionID)
        r = requests.post(url=url, data=json.dumps(template), headers=headers, verify=False)
        checkResponse(r)
        requestid = r.headers['location'].split('/')[7]
        return requestid

    #this is broken for our version of vRA and I haven't succesfully fixed yet. Leave alone for now.
    def provisionCatalogItem(self, catalogItem, forWhom="", requestDescription=None, reason=None,
                             vmDescription=None, vmLeaseDays=None, vmMemorySize=None,
                             vmCpuCount=None, businessGroupId=None, params={}, prepareOnly=False):
        requestData = {
            "@type": "CatalogItemRequest",
            "catalogItemRef": {
                "id": catalogItem["id"]
            },
            "organization": catalogItem["organization"],
            "requestedFor": forWhom,
            "businessGroupId": businessGroupId,
            "state": "UNSUBMITTED" if prepareOnly else "SUBMITTED",
            "requestNumber": 0,
            "requestData": {
                "entries": [{
                    "key": "provider-blueprintId",
                    "value": {
                        "type": "string",
                        "value": catalogItem["providerBinding"]["bindingId"]
                    }
                },
                {
                    "key": "provider-provisioningGroupId",
                    "value": {
                        "type": "string",
                        "value": catalogItem["organization"]["subtenantRef"]
                    }
                },
                {
                    "key": "requestedFor",
                    "value": {
                        "type": "string",
                        "value": forWhom
                    }
                },
                # {
                    # "key": "provider-VirtualMachine.Disk0.Size",
                    # "value": {
                        # "type": "string",
                        # "value": "1"
                    # }
                # },
                # {
                    # "key": "provider-VirtualMachine.Disk0.Letter",
                    # "value": {
                        # "type": "string",
                        # "value": "C"
                    # }
                # },
                # {
                    # "key": "provider-VirtualMachine.Disk0.Label",
                    # "value": {
                        # "type": "string",
                        # "value": "main"
                    # }
                # }
                ]
            }
        }
        params = params.copy()
        if requestDescription is not None:
            params["description"] = requestDescription
        if reason is not None:
            params["reasons"] = reason
        if vmDescription is not None:
            params["provider-__Notes"] = vmDescription
        if vmLeaseDays is not None:
            params["provider-VirtualMachine.LeaseDays"] = vmLeaseDays
        if vmMemorySize is not None:
            params["provider-VirtualMachine.Memory.Size"] = vmMemorySize
        if vmCpuCount is not None:
            params["provider-VirtualMachine.CPU.Count"] = vmCpuCount
        for key, value in params.items():
            if isinstance(value, int):
                type = "integer"
            else:
                type = "string"
            struct = {"key": key, "value": {"type": type, "value": value}}
            requestData["requestData"]["entries"].append(struct)
        return self.requestResource(requestData)
