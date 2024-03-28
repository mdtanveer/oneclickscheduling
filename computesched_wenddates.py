from projectclient import fetch_full_data
import processscheduler as ps
import jmespath
import json, sys
from datetime import datetime
from schedutil import add_working_days_to_date, count_working_days_between_days, str_to_date

OPTIONS = {'friendly_names': False}

force_fetch = False
if len(sys.argv) > 1 and sys.argv[1] == "-f":
    print("Force Fetching")
    force_fetch = True
projclient = fetch_full_data(force_fetch)

pb_bs = ps.SchedulingProblem(name="1-click scheduling")#,
        #delta_time=timedelta(days=1),
        #start_time = datetime.now())

class ExternalMapping:
    def __init__(self):
        self.tasks = {}
        self.resources = {}
        self.assignments = {}
        self.assignments_taskId2assId = {}
        self.tasks_json = {}

MAP = ExternalMapping()

project_day0 = datetime.today().date()
print("day0=", project_day0)

# resources
assignees = set(jmespath.search('[*].resourceId', projclient.data["assignments"]))
for resourceId in assignees:
    resource = jmespath.search(f'[?id == `{resourceId}`]', projclient.data["resources"])[0]
    resFriendlyName = resource["name"].rsplit(' ', 1)[0]
    r = ps.Worker(name=resFriendlyName if OPTIONS['friendly_names'] else resource['id'])
    MAP.resources[resource["id"]] = r

# assignments
for assignment in projclient.data["assignments"]:
    taskId = assignment['taskId']    
    resourceId = assignment['resourceId']
    assignmentId = assignment["id"]
    resource = MAP.resources[resourceId]    
    if taskId in MAP.assignments.keys():
        MAP.assignments[taskId].append(resource)
        MAP.assignments_taskId2assId[taskId].append(assignmentId)
    else:
        MAP.assignments[taskId] = [resource]
        MAP.assignments_taskId2assId[taskId] = [assignmentId]

## tasks
for task in projclient.data["tasks"]:
    if task['percentComplete'] == 100:
        continue
    taskname = task['name'] if OPTIONS['friendly_names'] else task['id']
    duration = int(int(task['duration'])/28800*1.5)
    priority = 10-task['priority']
    num_assignments = len(MAP.assignments_taskId2assId[task['id']]) if task['id'] in MAP.assignments_taskId2assId.keys() else 0
    if num_assignments > 1:
        duration /= num_assignments
    t = ps.FixedDurationTask(name=taskname, duration=int(duration), priority=priority)
    MAP.tasks[task['id']] = t
    MAP.tasks_json[task['id']] = task

# dependencies
for link in projclient.data["links"]:
    predessorTask = MAP.tasks[link['predecessorId']]    
    successorTask = MAP.tasks[link['successorId']]    
    ps.TaskPrecedence(task_before=predessorTask, task_after=successorTask, kind='lax')

for taskId in MAP.tasks.keys():
    task = MAP.tasks[taskId]
    if taskId not in MAP.assignments.keys():
        task.add_required_resource(ps.SelectWorkers(list_of_workers=MAP.resources.values(), nb_workers_to_select=1))
    else:
        for resource in MAP.assignments[taskId]:
            task.add_required_resource(resource)
    #taskEnd = count_working_days_between_days(project_day0, str_to_date(MAP.tasks_json[taskId]['finish']))
    #ps.TaskEndBefore(task=task, value=taskEnd, kind="strict")

# add makespan objective
ps.ObjectiveMinimizeMakespan()
ps.ObjectiveTasksStartEarliest(tasks=MAP.tasks.values())
#ps.ObjectiveMaximizeResourceUtilization(resource=MAP.resources.value())

# plot solution
solver = ps.SchedulingSolver(problem=pb_bs)

for r in MAP.resources.values():
    res_utilization = ps.IndicatorResourceUtilization(resource=r)
solution = solver.solve()

if not OPTIONS["friendly_names"]:
    print(solution.to_json())
    task_solution = json.loads(solution.to_json())

    task_starts = jmespath.search('tasks.*.{taskId: name, start: start, end: end}', task_solution)
    for task_start in task_starts:
        start_offset = task_start["start"]
        start = add_working_days_to_date(project_day0, start_offset) 
        end_offset = task_start["end"]
        end = add_working_days_to_date(project_day0, end_offset) 
        print(task_start["taskId"], task_start["start"], start, task_start["end"], end)
        projclient.delete_duration(task_start["taskId"])

        # "2023-09-21T16:00:00.000Z"
        projclient.update_task(task_start["taskId"], {'start': start.strftime("%Y-%m-%dT16:00:00.000Z"), 'finish': end.strftime("%Y-%m-%dT16:00:00.000Z")})
else:
    print(solution.to_json())
    print(solution.indicators)
    ps.render_gantt_matplotlib(solution)



