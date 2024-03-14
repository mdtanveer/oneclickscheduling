import requests
import json
import pyperclip
import os, logging
from pathlib import Path

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 0

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

class ProjectClient:
    def __init__(self, projectId, cdsUrl):
        clip = pyperclip.paste()
        if clip.startswith('Bearer '):
            with open("aadtoken.txt", "w") as f:
                f.write(clip.replace("Bearer ", ""))
        with open("aadtoken.txt") as f:
            self.aad_token = f.read()
        self.pcs_token = None
        self.projectId = projectId.upper()
        self.cdsUrl = cdsUrl
        self.work_dir = Path.cwd().joinpath('json', self.projectId)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.data = {
                "tasks": None,
                "resources": None,
                "assignments": None,
                "links": None
                }
        self.data_filters = {
                "tasks": "/?$select=name,duration,index,summary",
                "resources": None,
                "assignments": "/?$select=taskId,resourceId",
                "links": "/?$select=driver,predecessorId,successorId,linkType"
                }
        self.is_project_open = False

    def fetch_aad_token(self):
        if not self.aad_token:
            jsondata = json.load(open('json/project_auth.json'))
            x = requests.post("https://login.microsoftonline.com/common/oauth2/token",
                data=jsondata
            )
            x.raise_for_status()
            self.aad_token =  x.json()["access_token"]

    def get_headers(self):
        return {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "authority": "oneproject-ppe-torus-wus-azsc-000.project.microsoft.com",
                "authorization": None,
                "content-type": "application/json",
                "origin": "https://portfolios.officeppe.com",
                "referer": "https://portfolios.officeppe.com/",
                "sec-ch-ua": "\"Chromium\";v=\"116\", \"Not)A;Brand\";v=\"24\", \"Microsoft Edge\";v=\"116\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76",
                "viewportdefinition": "{\"selects\":[\"/project/tasks?$select=gridColor,name,blockDelete,start,finish,duration,index,critical,percentComplete,manual,milestone,outlineLevel,outlineNumber,work,actualWork,remainingWork,bucketId,bucketOrder,summary,notes,durationDisplayFormat,completeThrough,scheduleDrivers,constraintType,constraintDate,collapsed,includeAllCustomFields,cdsPercentComplete,cdsEffortRemaining,cdsEffortCompleted,cdsEffortEstimateAtComplete,cdsScheduleVariance,priority,sprintId,sprintOrder&$expand=assignments($select=taskId,percentWorkComplete,resourceId&$expand=resource($select=name,bookableResourceId,userPrincipalName,generic)),predecessors,successors,parent($select=),conversations($select=teamsConversationId, teamsChannelId)\",\"/project/tasks/fields?$select=name,type,rollup&$expand=values\",\"/project/links?$select=driver,predecessorId,successorId,linkType,delay,delayUnits\",\"/project?$select=name,percentComplete,workTemplateId,projectStart,hoursPerDay,duration,hoursPerWeek,daysPerMonth,latestTaskFinish,calendarId,hasCustomCalendar,ignoreResourceCalendars,earliestTaskStart,durationInDays,work,actualWork,remainingWork,taskDefaultFinishTime,taskDefaultStartTime,timezoneName,timezoneOffset,timezone,officeGroupId,projectState,projectManagerAadId,defaultSprintCreated\",\"/project/conditionalColoringRules\",\"/project/attachments?$select=taskId,uri,name,type,showOnCard\",\"/project/checklistItems?$select=taskId,name,completed,order\",\"/project/buckets?$select=name,order,color\",\"/project/sprints\",\"/project/views/grid\",\"/project/resources?$select=name,bookableResourceId,userPrincipalName,generic,aadId,jobTitle,type,aadUserType\",\"/project/labels\",\"/project/labelassociations\",\"/project/goals\",\"/project/goalAssociations\"]}",
                "x-project-client-type": "ModernProjectFamily",
            }

    def get_headers_with_authz(self):
        headers = self.get_headers()
        headers["authorization"] = f"Bearer {self.aad_token}"
        headers["x-project-sessiontoken"] = self.pcs_session_token
        return headers


    def open_project(self):
        if self.is_project_open:
            return

        headers = self.get_headers()
        headers["authorization"] = f"Bearer {self.aad_token}"
        x = requests.post("https://portfolios.officeppe.com/pss/api/v1.0/xrm/openproject",
            data=f'{{"xrmUrl":"{self.cdsUrl}","xrmProjectId":"{self.projectId}"}}',
            headers=headers
        )

        x.raise_for_status()
        data = x.json()
        self.pcs_token = data["accessToken"]
        self.aad_token = data["aadToken"]
        self.pcs_url = data["projectSessionApiUrl"]
        self.pcs_session_token = data["projectSessionToken"]
        self.is_project_open = True
        return data

    def get_projectdata_helper(self, suffix, filt = None):
        if not self.pcs_token or not self.pcs_url:
            raise
    
        headers = self.get_headers_with_authz()
        
        target_url = f"{self.pcs_url}/{suffix}"
        if filt:
            target_url += filt

        x = requests.get(target_url,
            headers=headers,
            cookies={},
            auth=(),
        )
        x.raise_for_status()
        return x.json()

    def fetch_full_data(self):
        DATA_SUFFIXES = self.data.keys() 
        read_keys = list(DATA_SUFFIXES) + ["project"]
        try:
            for suffix in read_keys:
                filename = suffix.split("/")[-1]
                file = self.work_dir.joinpath(f"{filename}.json")
                with open(file) as f:
                    self.data[suffix] = json.loads(f.read())
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            data = self.open_project()
            with open(self.work_dir.joinpath('project.json'), "w") as fout:
                fout.write(json.dumps(data, indent=4))
            for suffix in DATA_SUFFIXES:
                filename = suffix.split("/")[-1]
                print(f"Fetching...{suffix}")
                data = self.get_projectdata_helper(suffix, self.data_filters[suffix])
                self.data[suffix] = data
                with open(self.work_dir.joinpath(f"{filename}.json"), "w") as fout:
                    fout.write(json.dumps(data, indent=4))

    def get_incremental_data(self, revId):
        return self.get_projectdata_helper(f"?$since={revId}")

    def update_task(self, taskId, payload):
        self.open_project()
        target_url = f"{self.pcs_url}/tasks({taskId})"
        requests.patch(target_url,
            json = payload,
            headers = self.get_headers_with_authz()
            )

    def create_assignment(self, taskId, resource):
        self.open_project()
        target_url = f"{self.pcs_url}/assignments"
        requests.post(target_url,
            json={
                "taskId":taskId,
                "resourceId": resource["id"],
                "resourceName": resource["name"],
                "resourceTag":1,
                "resourceType":"XrmUser",
                "bookableResourceId": resource["bookableResourceId"],
                "skipNotification": True,
                },
            headers=self.get_headers_with_authz()
            )

def fetch_full_data():
    proj_client = ProjectClient("14c39a2e-7998-4dca-83b4-1d13c2fa39e6", "https://msdefault.crm.dynamics.com")
    proj_client.fetch_full_data()
    return proj_client

def fetch_incremental_data():
    proj_client = ProjectClient()
    #proj_client.fetch_aad_token()
    proj_client.open_project("https://msdefault.crm.dynamics.com", "b9238313-9e29-4cde-88cc-2fb4673fc4b9")
    data = proj_client.get_incremental_data("msxrm_msdefault.crm.dynamics.com_7575f8b2-3989-4878-86e2-d65c434c4562_0000000004") 
    return data

if __name__ == "__main__":
    projclient = fetch_full_data()
