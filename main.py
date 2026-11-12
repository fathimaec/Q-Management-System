import re
import sqlite3
from database import connect_db

def validate_password(password):
    p=r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
    if not re.match(p,password):
        print("\nInvalid password..")
        print("Password must contain at least 8 characters, one uppercase, one lowercase, one number and one special character.")
        return False
    return True
    

def register():
    name=input("\nEnter your full name     : ")
    user_name=input("Enter the username       : ")
    while True:
        password=input("Enter the password      : ")
        if validate_password(password):
            break
    conn=connect_db()
    c=conn.cursor()
    try:
        c.execute("""
                  INSERT INTO Users(full_name,user_name,password)
                  VALUES(?,?,?)""",(name,user_name,password))
        conn.commit()
        print("Registration successfull..!")
    except sqlite3.IntegrityError:
        print("Username already exists!")
    conn.close()


def login():
    user_name=input("\nEnter username      : ")
    password=input("Enter the password   : ")
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
             SELECT * FROM Users 
             WHERE user_name=? AND password=?""",(user_name,password))
    user=c.fetchone()
    conn.close()
    if user:
        print("Login Successful... Welcome",user[1])
        customer_dashboard(user)
    else:
        print("Invalid username or password")


#------------------------------------------------- ADMIN------------------------------------------------
def admin_login():
    user_name=input("Enter admin username : ")
    password=input("Enter the password    : ")
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              SELECT * FROM Admin 
              WHERE user_name=? AND password=?""",(user_name,password))
    admin=c.fetchone()
    conn.close()
    if admin:
        print("\nLogin successful...")
        print("Welcome Admin!")
        admin_dashboard()
    else:
        print("Invalid admin username or password..")


def admin_dashboard():
    while True:
        print("\n","="*40)
        print("             ADMIN DASHBOARD         ")
        print("="*40)
        print("1.View Waiting Queue")
        print("2.Call Next Customer")
        print("3.Complete Service")
        print("4.View Queue History")
        print("5.Mark Absent")
        print("6.Logout")

        ch=input("\nEnter your choice : ")
        if ch=="1":
            view_waiting_queue()
        elif ch=="2":
            call_next_customer()
        elif ch=="3":
            complete_service()
        elif ch=="4":
            view_queue_history()
        elif ch=="5":
            mark_absent()
        elif ch=="6":
            print("Logged ot successfully..!")
            break
        else:
            print("Invalid choice")
        input("Press enter to return to Dashboard...")


def view_waiting_queue():
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
             SELECT Queue.token_number,Users.full_name,Queue.status FROM Queue
             JOIN Users ON Queue.user_id=Users.user_id
             WHERE Queue.status='WAITING'
             AND Queue.service_date=DATE('now')
             ORDER BY Queue.token_number""")
    result=c.fetchall()
    conn.close()
    if result:    #check any customers are waiting
        print("="*20,"WAITING QUEUE","="*20)
        for token in result:
            print("\nToken Number   : ",str(token[0]).zfill(3))
            print("Customer Name    : ",token[1])
            print("Status           : ",token[2])
    else:
        print("\nNo customers are waiting..")
        


def call_next_customer():
    conn=connect_db()
    c=conn.cursor()
    #Check whether someone is already being served
    c.execute("""
              SELECT queue_id FROM Queue
              WHERE status='SERVING'
              AND service_date=DATE('now')""")
    if c.fetchone() is not None:
        print("Please complete the current service first!")
        conn.close()
        return
    #Find the first customer waiting in the queue
    c.execute("""
              SELECT queue_id, token_number
              FROM Queue
              WHERE status='WAITING'
              AND service_date=DATE('now')
              ORDER BY queue_id ASC LIMIT 1""")
    customer=c.fetchone()
    if customer is None:
        print("No customers are waiting!")
    else:
        queue_id=customer[0]
        token_number=customer[1]
        # Change the customer's status to SERVING
        c.execute("""
                  UPDATE Queue
                  SET status='SERVING',
                      called_at=CURRENT_TIMESTAMP
                  WHERE queue_id=?""",(queue_id,))
        conn.commit()
        print("================================")
        print("       CUSTOMER CALLED          ")
        print("================================")
        print("Token Number   :",str(token_number).zfill(3))
        print("Status         : SERVING")
    conn.close()


def complete_service():
    conn=connect_db()
    c=conn.cursor()
    # Find the customer currently being served
    c.execute("""
        SELECT queue_id, token_number
        FROM Queue
        WHERE status = 'SERVING'
        AND service_date = DATE('now')
        ORDER BY called_at ASC LIMIT 1
    """)
    customer=c.fetchone()
    if customer is None:
        print("No customer is currently being served!")
    else:
        queue_id=customer[0]
        token_number=customer[1]
        # Update the customer's status
        c.execute("""
            UPDATE Queue
            SET status='COMPLETED',
                completed_at=CURRENT_TIMESTAMP
            WHERE queue_id=?
        """, (queue_id,))
        conn.commit()
        print("Service completed successfully!!")
        print("Token Number : ", str(token_number).zfill(3))
        print("Status       : COMPLETED")
    conn.close()


def view_queue_history():
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              SELECT Queue.token_number,
                     Users.full_name,
                     Queue.created_at,
                     Queue.called_at,
                     Queue.completed_at,
                     Queue.status
              FROM Queue
              JOIN Users ON Queue.user_id=Users.user_id
              WHERE Queue.status IN('COMPLETED','SKIPPED')
              ORDER BY Queue.queue_id DESC""")
    history=c.fetchall()
    conn.close()
    if history:
        print("="*20,"QUEUE HISTORY","="*20)
        for q in history:
            print("Token number  : ",str(q[0]).zfill(3))
            print("Customer name : ",q[1])
            print("Joined at     : ",q[2])
            print("Called at     : ",q[3] if q[3] else "-")
            print("Completed at  : ",q[4] if q[4] else "-")
            print("status        : ",q[5])
            print("-"*50)
        print("Total completed customers : ",len(history))
    else:
        print("No completed records found..")


def mark_absent():
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              SELECT token_number FROM Queue
              WHERE status='SERVING' AND service_date=DATE('now')""")
    customer=c.fetchone()
    if customer:
        c.execute("""
                  UPDATE Queue SET status='SKIPPED'
                  WHERE status='SERVING'
                  AND service_date=DATE('now')""")
        conn.commit()
        print("Customer marked as Absent..!")
        print("Token number    : ",str(customer[0]).zfill(3))
    else:
        print("No customer is currently being served..")
    conn.close()
        
#------------------------------------------------- ADMIN------------------------------------------------


#--------------------------------------------------CUSTOMER----------------------------------------------
def customer_dashboard(user):
    while True:
        print("\n","="*40)
        print("           Dashbaord   ")
        print("="*40)
        print("welcome",user[1])
        print("\n1.Join Queue")
        print("2.My Token")
        print("3.Check Queue Status")
        print("4.Logout")
        ch=input("Enter your choice : ")
        if ch=="1":
            join_queue(user)
        elif ch=="2":
            my_token(user)
        elif ch=="3":
            check_queue_status(user)
        elif ch=="4":
            print("Logged out successfully")
            break
        else:
            print("Invalid choice")


def join_queue(user):
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              SELECT token_number FROM Queue
              WHERE user_id=? AND service_date=DATE('now')"""
              ,(user[0],))
    present=c.fetchone()
    if present:
        print("You are already joined in the queue today!")
        print("Your Token number is : ",str(present[0]).zfill(3))
    else:
        c.execute("""
                SELECT MAX(token_number) FROM Queue 
                WHERE service_date=DATE('now')""")
        result=c.fetchone()
        if result[0] is None:
            token_number=1
        else:
            token_number=result[0]+1
        c.execute("""
                INSERT INTO Queue(user_id,token_number)
                VALUES(?,?)""",(user[0],token_number))
        conn.commit()
        print("You have successfully joined in the queue!")
        print("Your Token number is : ",str(token_number).zfill(3))
        print("Status               : Waiting..")
    conn.close()
    input("\nPress enter to return to Dashboard...")
 

def my_token(user):
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              SELECT token_number,status from Queue
              WHERE user_id=? AND service_date=DATE('now')
              ORDER BY queue_id DESC LIMIT 1""",(user[0],))
    result=c.fetchone()
    conn.close()
    if result:
        print("\nYour token number  : ",str(result[0]).zfill(3))
        print("Status               : ",result[1])
    else:
        print("You are not joined in the queue yet")
    input("\nPress enter to return to Dashboard...")



def check_queue_status(user):
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              SELECT token_number,status FROM Queue
              WHERE user_id=? AND service_date=DATE('now')
              ORDER BY queue_id DESC LIMIT 1""",(user[0],))

    result=c.fetchone()
    if result:
        token_number=result[0]
        status=result[1]
        #Count customers waiting ahead
        c.execute("""
                  SELECT COUNT(*) FROM Queue
                  WHERE token_number<? AND status='WAITING'
                  AND service_date=DATE('now')""",(token_number,))
        token=c.fetchone()[0]
        #Calculate average service waiting time
        c.execute("""
                  SELECT AVG((julianday(completed_at)-julianday(called_at))*1440)
                  FROM Queue WHERE status='COMPLETED'
                  AND called_at IS NOT NULL
                  AND completed_at IS NOT NULL""")

        avg=c.fetchone()[0]
        if avg is None:
            avg=10
        #Check current serving customer
        c.execute("""
                  SELECT (julianday('now')-julianday(called_at))*1440
                  FROM Queue WHERE status='SERVING'
                  AND service_date=DATE('now')
                  ORDER BY called_at ASC LIMIT 1""")
        serving=c.fetchone()
        remaining=0
        if serving and serving[0] is not None:
            front=serving[0]
            remaining=max(0,avg-front)
        waiting_time=(token*avg)+remaining
        print("\nYour Token number  : ",str(token_number).zfill(3))
        print("Status               : ",status)

        if status=="WAITING":
            print("People ahead           : ",token)
            print("Estimated waiting time : ",round(waiting_time),"minutes")

        elif status=="SERVING":
            print("Your service is currently in progress..")

        elif status=="COMPLETED":
            print("Your service is completed.")

        elif status=="SKIPPED":
            print("You were marked as Absent.")
    else:
        print("You are not joined in the queue today..")
    conn.close()
    input("Press enter to return to dashboard...")

#--------------------------------------------------CUSTOMER----------------------------------------------


while True:
    print("\n1.Sign Up")
    print("2.Customer Login")
    print("3.Admin Login")
    print("4.Exit")
    ch=input("Enter your choice(1,2,3,4) : ")
    if ch=="1":
        register()
    elif ch=="2":
        login()
    elif ch=="3":
        admin_login()
    elif ch=="4":
        print("Thankyouu!!")
        break
    else:
        print("Invalid choice")
    
