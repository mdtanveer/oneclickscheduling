from datetime import datetime, timedelta
import numpy as np

def add_working_days_to_date_old(start_date, days_to_add):
    from datetime import timedelta
    start_weekday = start_date.weekday()

    # first week
    total_days = start_weekday + days_to_add
    if total_days < 5:
        return start_date + timedelta(days=days_to_add)
    else:
        # first week
        total_days = 7 - start_weekday
        days_to_add -= 5 - start_weekday

        # middle whole weeks
        whole_weeks = days_to_add // 5
        remaining_days = days_to_add % 5
        total_days += whole_weeks * 7
        days_to_add -= whole_weeks * 5

        # last week
        total_days += remaining_days

        return start_date + timedelta(days=total_days)

def add_working_days_to_date(start_date, days_to_add):
    return np.busday_offset(start_date, days_to_add, roll='forward').astype(datetime)

def add_working_days_to_date_str(start, days_to_add):
    start_date =  datetime.strptime(start, '%Y-%m-%d').date()
    return np.busday_offset(start_date, days_to_add, roll='forward').astype(datetime)

def count_working_days_between_days(start_date, end_date):
    return np.busday_count(start_date, end_date)

def str_to_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').date()

def count_working_days_between_days_str(start, end):
    start_date =  datetime.strptime(start, '%Y-%m-%d').date()
    end_date =  datetime.strptime(end, '%Y-%m-%d').date()
    return np.busday_count(start_date, end_date)

