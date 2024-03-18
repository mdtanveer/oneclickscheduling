from projectclient import fetch_full_data
import processscheduler as ps
import jmespath
import json
from datetime import datetime
from schedutil import add_working_days_to_date, count_working_days_between_days, str_to_date

OPTIONS = {'friendly_names': False}

projclient = fetch_full_data()

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

project_day0 = projclient.get_day0()
print("day0=", project_day0)

# resources
for resource in projclient.data["resources"]:
    resFriendlyName = resource["name"].rsplit(' ', 1)[0]
    r = ps.Worker(name=resFriendlyName if OPTIONS['friendly_names'] else resource['id'])
    MAP.resources[resource["id"]] = r

# tasks
for task in projclient.data["tasks"]:
    taskname = task['name'] if OPTIONS['friendly_names'] else task['id']
    t = ps.FixedDurationTask(name=taskname, duration=int(int(task['duration'])/28800))
    MAP.tasks[task['id']] = t
    MAP.tasks_json[task['id']] = task

# dependencies
for link in projclient.data["links"]:
    predessorTask = MAP.tasks[link['predecessorId']]    
    successorTask = MAP.tasks[link['successorId']]    
    ps.TaskPrecedence(task_before=predessorTask, task_after=successorTask, kind='tight')

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
for taskId in MAP.tasks.keys():
    task = MAP.tasks[taskId]
    if taskId not in MAP.assignments.keys():
        task.add_required_resource(ps.SelectWorkers(list_of_workers=MAP.resources.values(), nb_workers_to_select=1))
    else:
        if len(MAP.assignments[taskId]) > 1:
            task.add_required_resource(ps.SelectWorkers(list_of_workers=MAP.assignments[taskId], nb_workers_to_select=1))
        elif len(MAP.assignments[taskId]) == 1:
            task.add_required_resource(MAP.assignments[taskId][0])
            taskStart = count_working_days_between_days(project_day0, str_to_date(MAP.tasks_json[taskId]['start']))
            ps.TaskStartAt(task=task, value=taskStart)

# add makespan objective
ps.ObjectiveMinimizeMakespan()

# plot solution
solver = ps.SchedulingSolver(problem=pb_bs)

for r in MAP.resources.values():
    res_utilization = ps.IndicatorResourceUtilization(resource=r)
solution = solver.solve()

if not OPTIONS["friendly_names"]:
    task_solution = json.loads(solution.to_json())

    #clean up multi assignments
    for taskId in MAP.assignments_taskId2assId.keys():
        if len(MAP.assignments_taskId2assId[taskId]) > 1:
            for assId in MAP.assignments_taskId2assId[taskId]:
                projclient.delete_assignment(assId)

    assignments = jmespath.search('tasks.*.{taskId: name, resId: assigned_resources[0]}', task_solution)
    for assignment in assignments:
        #print(assignment["taskId"], assignment["resId"])
        resource = jmespath.search(f'[?id == `{assignment["resId"]}`]', projclient.data["resources"])[0]
        projclient.create_assignment(assignment["taskId"], resource)

    task_starts = jmespath.search('tasks.*.{taskId: name, start: start}', task_solution)
    for task_start in task_starts:
        start_offset = task_start["start"]
        start = add_working_days_to_date(project_day0, start_offset) 
        print(task_start["taskId"], task_start["start"], start)

        # "2023-09-21T16:00:00.000Z"
        projclient.update_task(task_start["taskId"], {'start': start.strftime("%Y-%m-%dT16:00:00.000Z")})
else:
    print(solution.to_json())
    print(solution.indicators)
    ps.render_gantt_matplotlib(solution)



