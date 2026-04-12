from mcp.server.fastmcp import FastMCP
from typing import Literal
from datetime import datetime
import uuid

mcp = FastMCP("Enterprise_IT_Server")

# Mock Database

EMPLOYEE_DB = {
    "E1001": {"name": "Alice Chen", "department": "Engineering", "title": "Backend Developer", "manager_id": "E1005", "status": "Active"},
    "E1002": {"name": "Bob Lin", "department": "Engineering", "title": "Frontend Developer", "manager_id": "E1005", "status": "Active"},
    "E1003": {"name": "Charlie Wang", "department": "Sales", "title": "Account Manager", "manager_id": "E1008", "status": "Active"},
    "E1004": {"name": "David Wu", "department": "HR", "title": "HR Specialist", "manager_id": "E1009", "status": "Leave"},
}

LEAVE_BALANCE_DB = {
    "E1001": {"annual_leave": 14, "sick_leave": 5, "comp_time": 24}, # comp_time's unit is hour
    "E1002": {"annual_leave": 7, "sick_leave": 2, "comp_time": 0},
    "E1003": {"annual_leave": 21, "sick_leave": 10, "comp_time": 8},
    "E1004": {"annual_leave": 0, "sick_leave": 0, "comp_time": 0},
}

TICKET_DB = {}

# MCP Tools

@mcp.tool()
def get_employee_profile(emp_id: str) -> str:
    emp_id = emp_id.strip().upper()
    emp = EMPLOYEE_DB.get(emp_id)
    if not emp:
        return f"ERROR: Cannot find employee ID {emp_id}, please enter a valid id."
    
    return (
        f" Employee's Info \n"
        f"Name: {emp['name']}\n"
        f"Department: {emp['department']}\n"
        f"Title: {emp['title']}\n"
        f"Manager ID: {emp['manager_id']}\n"
        f"Status: {emp['status']}"
    )

@mcp.tool()
def query_leave_balance(emp_id: str, leave_type: Literal["annual_leave", "sick_leave", "comp_time", "all"] = "all") -> str:
    emp_id = emp_id.strip().upper()
    if emp_id not in EMPLOYEE_DB:
        return f"ERROR: Employee ID: {emp_id} not found."
    
    balances = LEAVE_BALANCE_DB.get(emp_id)

    if leave_type == "all":
        return (
            f"[{EMPLOYEE_DB[emp_id]['name']}'s Leave Balance] \n"
            f"Annual Leave: {balances['annual_leave']} days\n"
            f"Sick Leave: {balances['sick_leave']} days\n"
            f"Comp Time: {balances['comp_time']} hours"
        )
    
    # Query of specific type of leave
    type_mapping = {"annual_leave": "Annual Leave(days)", "sick_leave": "Sick Leave(days)", "comp_time": "Comp Time(hours)"}
    value = balances.get(leave_type)
    return f"{EMPLOYEE_DB[emp_id]['name']}'s {type_mapping[leave_type]} balance: {value}"

@mcp.tool()
def create_it_ticket(emp_id: str, category: Literal["Hardware", "Software", "Network", "Account_Access"], 
                     description: str, urgency: Literal["Low", "Medium", "High"] = "Medium") -> str:
    emp_id = emp_id.strip().upper()
    if emp_id not in EMPLOYEE_DB:
        return f"Failed to create ticket: Employee ID: {emp_id} not found."
    
    date_str = datetime.now().strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:4].upper()
    ticket_id = f"TKT-{date_str}-{short_uuid}"

    TICKET_DB[ticket_id] = {
        "requester": emp_id,
        "name": EMPLOYEE_DB[emp_id]['name'],
        "category": category,
        "description": description,
        "urgency": urgency,
        "status": "Open",
        "created_at": datetime.now().isoformat()
    }

    return (
        f"Successfully Created Ticket!\n"
        f"Ticket ID: {ticket_id}\n"
        f"Requester: {EMPLOYEE_DB[emp_id]['name']}\n"
        f"Category: {category} (Ungency: {urgency})\n"
        f"Description: {description}"
    )

@mcp.tool()
def query_ticket_status(ticket_id: str) -> str:
    ticket = TICKET_DB.get(ticket_id.strip().upper())
    if not ticket:
        return f"ERROR: Ticket ID {ticket_id} not found."
    
    return f"Ticket {ticket_id} status: {ticket['status']}. Created At: {ticket['created_at']}"

@mcp.resource("db://tickets")
def get_all_tickets() -> str:
    import json
    return json.dumps(TICKET_DB, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()