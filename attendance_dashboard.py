import customtkinter as ctk
from theme import *  # noqa: F401,F403
import sys
import time
import session_store as ss
from session_ui import identify_faculty, SessionBar, StartSessionDialog, RosterWindow
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
import cv2
import os
import json
import csv
from datetime import datetime


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STUDENT_FILE = os.path.join(
    BASE_DIR,
    "students.json"
)

ATTENDANCE_FILE = os.path.join(
    BASE_DIR,
    "attendance.json"
)


# =========================================================
# CREATE FILES IF NOT EXISTS
# =========================================================

if not os.path.exists(STUDENT_FILE):

    with open(
        STUDENT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            [],
            file,
            indent=4
        )


if not os.path.exists(ATTENDANCE_FILE):

    with open(
        ATTENDANCE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            [],
            file,
            indent=4
        )


# =========================================================
# PRIMARY + WHITE COLOR THEME
# =========================================================



# Main colors
















# =========================================================
# GLOBAL VARIABLES
# =========================================================

selected_student = None

camera_running = False


# =========================================================
# LOAD JSON
# =========================================================

def load_json(file_path):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except Exception:

        return []


# =========================================================
# SAVE JSON
# =========================================================

def save_json(file_path, data):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# LOAD STUDENTS
# =========================================================

def load_students():

    return load_json(STUDENT_FILE)


# =========================================================
# LOAD ATTENDANCE
# =========================================================

def load_attendance():

    return load_json(ATTENDANCE_FILE)


# =========================================================
# APPLICATION
# =========================================================

app = ctk.CTk()

app.title(
    "AI Smart Attendance Dashboard"
)

app.geometry(
    "1280x860"
)

app.minsize(
    1000,
    640
)

app.configure(
    fg_color=BG_COLOR
)

app.withdraw()

current_user = identify_faculty(app)

if current_user is None:
    app.destroy()
    sys.exit(0)

current_session = None

app.deiconify()
maximize(app)

fade_in(app)


# =========================================================
# HEADER
# =========================================================

header = ctk.CTkFrame(
    app,
    height=85,
    corner_radius=0,
    fg_color=INK
)

header.pack(
    fill="x"
)

header.pack_propagate(False)

gold_rule(app, 3).pack(fill="x")


# Header left

header_left = ctk.CTkFrame(
    header,
    fg_color="transparent"
)

header_left.pack(
    side="left",
    padx=30,
    pady=12
)


ctk.CTkLabel(
    header_left,
    text="AI SMART ATTENDANCE",
    font=(FONT_HEAD, 25, "bold"),
    text_color=WHITE
).pack(
    anchor="w"
)


ctk.CTkLabel(
    header_left,
    text="Face Recognition • Attendance Management • Reports",
    font=(FONT_BODY, 12),
    text_color="#D9C28F"
).pack(
    anchor="w"
)


# Logout

def logout():

    result = messagebox.askyesno(
        "Logout",
        "Are you sure you want to logout?\n\n"
        "Any live session of yours will be ended."
    )

    if result:

        shutdown()


logout_button = ctk.CTkButton(
    header,
    text="↪  Logout",
    width=115,
    height=38,
    corner_radius=10,
    fg_color=WHITE,
    hover_color=TINT,
    text_color=INK,
    font=(FONT_BODY, 13, "bold"),
    command=logout
)

logout_button.pack(
    side="right",
    padx=30
)

ctk.CTkLabel(
    header,
    text=f"{current_user['full_name']}  ·  {current_user['role']}",
    font=(FONT_BODY, 12, "bold"),
    text_color=GOLD_LIGHT,
    fg_color="#1E2C52",
    corner_radius=16,
    padx=16,
    pady=7
).pack(
    side="right",
    padx=(0, 4)
)


# =========================================================
# LIVE SESSION BAR
# =========================================================

session_bar = SessionBar(
    app,
    current_user,
    on_start=lambda: start_session_flow(),
    on_end=lambda: end_session_flow(),
    on_roster=lambda: open_roster()
)

session_bar.pack(
    fill="x",
    padx=28,
    pady=(16, 0)
)


# =========================================================
# SEARCH CARD
# =========================================================

search_card = ctk.CTkFrame(
    app,
    fg_color=WHITE,
    corner_radius=16,
    border_width=1,
    border_color=BORDER_COLOR
)

search_card.pack(
    fill="x",
    padx=28,
    pady=(12, 12)
)


ctk.CTkLabel(
    search_card,
    text="🔍  Search Student",
    font=(FONT_BODY, 16, "bold"),
    text_color=TEXT_COLOR
).pack(
    side="left",
    padx=(20, 10),
    pady=15
)


search_entry = ctk.CTkEntry(
    search_card,
    width=370,
    height=40,
    corner_radius=10,
    fg_color=WHITE,
    text_color=TEXT_COLOR,
    border_color=BORDER_COLOR,
    border_width=2,
    placeholder_text="Student ID / PRN / Name",
    placeholder_text_color="#9B9486"
)

search_entry.pack(
    side="left",
    pady=15
)


# =========================================================
# SEARCH FUNCTION
# =========================================================

def search_student():

    global selected_student

    if current_session is None:

        messagebox.showwarning(
            "No Active Session",
            "Start an attendance session first.\n\n"
            "Click 'Start Session' at the top, choose your class "
            "and students, then search within your roster."
        )

        return

    query = search_entry.get().strip().lower()

    if query == "":

        messagebox.showwarning(
            "Search Student",
            "Please enter Student ID, PRN or Student Name."
        )

        search_entry.focus()

        return


    def hits(student):

        return (
            query in str(student.get("student_id", "")).lower()
            or query in str(student.get("prn", "")).lower()
            or query in str(student.get("name", "")).lower()
        )


    students = load_students()

    roster_ids = set(current_session["student_ids"])

    matches = [
        student for student in students
        if str(student.get("student_id")) in roster_ids and hits(student)
    ]


    if len(matches) == 0:

        outside = [student for student in students if hits(student)]

        if len(outside) == 0:

            messagebox.showinfo(
                "Student Not Found",
                "No student found.\n\n"
                "Please check Student ID, PRN or Name."
            )

            return

        student = outside[0]

        holder = ss.busy_students(
            exclude_session_id=current_session["session_id"]
        ).get(str(student.get("student_id")))

        if holder:

            messagebox.showinfo(
                "In Another Session",
                f"{student.get('name', 'This student')} is currently in "
                f"{holder['faculty_name']}'s live session "
                f"({holder['subject']}, {holder['class']}-{holder['division']}).\n\n"
                "A student can only be in one live session at a time."
            )

        else:

            messagebox.showinfo(
                "Not In Your Session",
                f"{student.get('name', 'This student')} is not on "
                "your session's roster."
            )

        return


    selected_student = matches[0]

    update_student_profile(
        selected_student
    )

    update_attendance_summary()

    update_history()


    if len(matches) > 1:

        messagebox.showinfo(
            "Multiple Students",
            f"{len(matches)} students found.\n\n"
            "First matching student selected."
        )


# Search button

ctk.CTkButton(
    search_card,
    text="SEARCH",
    width=100,
    height=40,
    corner_radius=10,
    fg_color=PRIMARY,
    hover_color=PRIMARY_HOVER,
    text_color=WHITE,
    font=(FONT_BODY, 12, "bold"),
    command=search_student
).pack(
    side="left",
    padx=10
)


# Registered students

student_count_label = ctk.CTkLabel(
    search_card,
    text="Registered Students: 0",
    font=(FONT_BODY, 12, "bold"),
    text_color=PRIMARY
)

student_count_label.pack(
    side="right",
    padx=20
)


# =========================================================
# MAIN CONTENT
# =========================================================

content = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

content.pack(
    fill="both",
    expand=True,
    padx=28,
    pady=5
)


# =========================================================
# LEFT PROFILE CARD
# =========================================================

profile_card = ctk.CTkFrame(
    content,
    width=350,
    fg_color=WHITE,
    corner_radius=18,
    border_width=1,
    border_color=BORDER_COLOR
)

profile_card.pack(
    side="left",
    fill="y",
    padx=(0, 12)
)

profile_card.pack_propagate(False)


# Profile title

ctk.CTkLabel(
    profile_card,
    text="👤  Student Profile",
    font=(FONT_HEAD, 21, "bold"),
    text_color=INK
).pack(
    anchor="w",
    padx=22,
    pady=(14, 8)
)


# =========================================================
# PROFILE PHOTO
# =========================================================

profile_photo = ctk.CTkLabel(
    profile_card,
    text="👤\n\nSelect Student",
    width=210,
    height=120,
    fg_color=TINT,
    corner_radius=15,
    text_color=MUTED_TEXT,
    font=(FONT_BODY, 14, "bold")
)

profile_photo.pack(
    pady=5
)


profile_status = ctk.CTkLabel(
    profile_card,
    text="No Student Selected",
    font=(FONT_BODY, 12, "bold"),
    text_color=MUTED_TEXT
)

profile_status.pack(
    pady=(5, 8)
)


# =========================================================
# PROFILE INFORMATION
# =========================================================

profile_fields = {}


def create_profile_row(
    title,
    key
):

    row = ctk.CTkFrame(
        profile_card,
        fg_color=LIGHT_GREY,
        corner_radius=8
    )

    row.pack(
        fill="x",
        padx=20,
        pady=2
    )


    ctk.CTkLabel(
        row,
        text=title,
        width=95,
        anchor="w",
        font=(FONT_BODY, 10, "bold"),
        text_color=MUTED_TEXT
    ).pack(
        side="left",
        padx=10,
        pady=5
    )


    value_label = ctk.CTkLabel(
        row,
        text="-",
        anchor="w",
        font=(FONT_BODY, 10, "bold"),
        text_color=TEXT_COLOR
    )

    value_label.pack(
        side="left",
        fill="x",
        expand=True,
        padx=3
    )


    profile_fields[key] = value_label


create_profile_row(
    "Name",
    "name"
)

create_profile_row(
    "Student ID",
    "student_id"
)

create_profile_row(
    "PRN",
    "prn"
)

create_profile_row(
    "Department",
    "department"
)

create_profile_row(
    "Class",
    "class"
)

create_profile_row(
    "Division",
    "division"
)


# =========================================================
# RIGHT CONTENT
# =========================================================

right_frame = ctk.CTkFrame(
    content,
    fg_color="transparent"
)

right_frame.pack(
    side="left",
    fill="both",
    expand=True
)


# =========================================================
# ATTENDANCE SUMMARY
# =========================================================

summary_frame = ctk.CTkFrame(
    right_frame,
    fg_color="transparent"
)

summary_frame.pack(
    fill="x",
    pady=(0, 12)
)


summary_values = {}


def create_summary_card(
    title,
    key,
    icon
):

    card = ctk.CTkFrame(
        summary_frame,
        fg_color=WHITE,
        corner_radius=15,
        border_width=1,
        border_color=BORDER_COLOR
    )

    card.pack(
        side="left",
        fill="both",
        expand=True,
        padx=5
    )

    card_accent(card, inset=18)


    ctk.CTkLabel(
        card,
        text=icon,
        font=(FONT_HEAD, 22)
    ).pack(
        anchor="w",
        padx=15,
        pady=(10, 0)
    )


    value = ctk.CTkLabel(
        card,
        text="0",
        font=(FONT_HEAD, 25, "bold"),
        text_color=INK
    )

    value.pack(
        anchor="w",
        padx=15
    )


    ctk.CTkLabel(
        card,
        text=title,
        font=(FONT_BODY, 11),
        text_color=MUTED_TEXT
    ).pack(
        anchor="w",
        padx=15,
        pady=(0, 12)
    )


    summary_values[key] = value


create_summary_card(
    "Total Lectures",
    "total",
    "📅"
)

create_summary_card(
    "Present",
    "present",
    "✓"
)

create_summary_card(
    "Absent",
    "absent",
    "✕"
)

create_summary_card(
    "Attendance %",
    "percentage",
    "%"
)


# =========================================================
# FACE RECOGNITION CARD
# =========================================================

camera_card = ctk.CTkFrame(
    right_frame,
    fg_color=WHITE,
    corner_radius=18,
    border_width=1,
    border_color=BORDER_COLOR
)

camera_card.pack(
    fill="x",
    pady=(0, 12)
)


camera_content = ctk.CTkFrame(
    camera_card,
    fg_color="transparent"
)

camera_content.pack(
    fill="x",
    padx=20,
    pady=18
)


ctk.CTkLabel(
    camera_content,
    text="📸  Face Recognition",
    font=(FONT_HEAD, 19, "bold"),
    text_color=INK
).pack(
    anchor="w"
)


ctk.CTkLabel(
    camera_content,
    text="Start camera and detect the registered student's face.",
    font=(FONT_BODY, 11),
    text_color=MUTED_TEXT
).pack(
    anchor="w",
    pady=(3, 8)
)


camera_status = ctk.CTkLabel(
    camera_content,
    text="Ready to recognize",
    font=(FONT_BODY, 12, "bold"),
    text_color=MUTED_TEXT
)

camera_status.pack(
    anchor="w"
)


# =========================================================
# MARK ATTENDANCE
# =========================================================

def mark_attendance():
    """Mark the selected student in my live session -> (status, detail)."""

    if selected_student is None:

        messagebox.showwarning(
            "Select Student",
            "Please search and select a student first."
        )

        return "none", None

    if current_session is None:

        return "inactive", None

    try:

        return ss.mark_attendance(
            current_session["session_id"],
            selected_student
        )

    except TimeoutError:

        return "busy", None


# =========================================================
# CAMERA FUNCTION
# =========================================================

def start_camera():

    global selected_student
    global current_session

    if current_session is None:

        messagebox.showwarning(
            "No Active Session",
            "Start an attendance session before opening the camera."
        )

        return

    if selected_student is None:

        messagebox.showwarning(
            "Student Required",
            "Please search for a student before starting the camera."
        )

        return


    camera_status.configure(
        text="Opening camera...",
        text_color=PRIMARY
    )

    app.update()


    # Camera

    cap = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )


    if not cap.isOpened():

        cap.release()

        cap = cv2.VideoCapture(
            0
        )


    if not cap.isOpened():

        camera_status.configure(
            text="Camera unavailable",
            text_color=RED
        )

        messagebox.showerror(
            "Camera Error",
            "Unable to open camera.\n\n"
            "Please check camera permission."
        )

        return


    # Face detector

    face_cascade = cv2.CascadeClassifier(
        cascade_path("haarcascade_frontalface_default.xml")
    )


    camera_status.configure(
        text="Camera Running • SPACE = Mark • Q = Exit",
        text_color=PRIMARY
    )


    session_lost = False

    last_beat = time.time()

    while True:

        # the camera loop blocks the window, so keep the session alive here
        if time.time() - last_beat > ss.HEARTBEAT_EVERY - 3:

            last_beat = time.time()

            if not ss.heartbeat(current_session["session_id"]):

                session_lost = True

                break

        ret, frame = cap.read()


        if not ret:

            break


        # Mirror camera

        frame = cv2.flip(
            frame,
            1
        )


        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )


        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)
        )


        # Draw face boxes

        for (
            x,
            y,
            w,
            h
        ) in faces:

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                CV_GOLD,
                3
            )


            cv2.putText(
                frame,
                "FACE DETECTED",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                CV_GOLD,
                2
            )


        # Top message

        cv2.putText(
            frame,
            "SPACE = MARK ATTENDANCE",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            "Q = EXIT",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.imshow(
            "AI Face Recognition",
            frame
        )


        key = cv2.waitKey(
            1
        ) & 0xFF


        # SPACE

        if key == 32:

            if len(faces) == 0:

                messagebox.showwarning(
                    "No Face Detected",
                    "No face detected.\n\n"
                    "Please position the student's face in front of the camera."
                )

            else:

                status, detail = mark_attendance()


                if status == "marked":

                    camera_status.configure(
                        text="✓ Attendance marked successfully",
                        text_color=GREEN
                    )

                    messagebox.showinfo(
                        "Attendance Successful",
                        "Attendance marked successfully!\n\n"
                        f"Student: {selected_student.get('name', '')}\n"
                        f"Subject: {current_session['subject']}\n"
                        f"Date: {datetime.now().strftime('%d-%m-%Y')}\n"
                        f"Time: {datetime.now().strftime('%H:%M:%S')}"
                    )

                elif status == "duplicate":

                    messagebox.showinfo(
                        "Already Present",
                        "This student has already been marked "
                        "present in this session."
                    )

                elif status == "not_in_roster":

                    holder_text = (
                        f"They are in {detail['faculty_name']}'s live session "
                        f"({detail['subject']})."
                        if detail else
                        "They are not on your session's roster."
                    )

                    messagebox.showwarning(
                        "Not In Your Session",
                        holder_text
                    )

                elif status == "inactive":

                    session_lost = True

                    break

                else:

                    messagebox.showerror(
                        "Please Try Again",
                        "The attendance data is busy right now. "
                        "Please try again in a moment."
                    )


                update_attendance_summary()

                update_history()


        # Q

        elif key == ord("q"):

            break


    cap.release()

    cv2.destroyAllWindows()


    camera_status.configure(
        text="Ready to recognize",
        text_color=MUTED_TEXT
    )

    if session_lost:

        messagebox.showwarning(
            "Session Ended",
            "Your attendance session is no longer active.\n\n"
            "Please start a new session to continue."
        )

        current_session = None

        on_session_changed()

    else:

        session_bar.set_marked(marked_count())


# Start camera button

ctk.CTkButton(
    camera_content,
    text="📷  START CAMERA",
    width=190,
    height=42,
    corner_radius=10,
    fg_color=PRIMARY,
    hover_color=PRIMARY_HOVER,
    text_color=WHITE,
    font=(FONT_BODY, 13, "bold"),
    command=start_camera
).pack(
    anchor="w",
    pady=(10, 0)
)


# =========================================================
# ATTENDANCE HISTORY
# =========================================================

history_card = ctk.CTkFrame(
    right_frame,
    fg_color=WHITE,
    corner_radius=18,
    border_width=1,
    border_color=BORDER_COLOR
)

history_card.pack(
    fill="both",
    expand=True
)


# History header

history_header = ctk.CTkFrame(
    history_card,
    fg_color="transparent"
)

history_header.pack(
    fill="x",
    padx=18,
    pady=(14, 5)
)


ctk.CTkLabel(
    history_header,
    text="📅  Attendance History",
    font=(FONT_HEAD, 18, "bold"),
    text_color=INK
).pack(
    side="left"
)


# =========================================================
# EXPORT FUNCTION
# =========================================================

def export_attendance():

    attendance = load_attendance()


    if selected_student:

        attendance = [

            record

            for record in attendance

            if record.get(
                "student_id"
            )
            ==
            selected_student.get(
                "student_id"
            )
        ]


    if not selected_student:

        attendance = [
            record
            for record in attendance
            if record.get("faculty_id", current_user["user_id"])
            == current_user["user_id"]
        ]


    if len(attendance) == 0:

        messagebox.showinfo(
            "Export",
            "No attendance records available."
        )

        return


    file_path = filedialog.asksaveasfilename(

        title="Export Attendance",

        defaultextension=".csv",

        filetypes=[
            (
                "CSV Files",
                "*.csv"
            )
        ]
    )


    if not file_path:

        return


    fields = [

        "student_id",
        "prn",
        "name",
        "date",
        "time",
        "status",
        "recognition",
        "subject",
        "class",
        "division",
        "faculty_name",
        "session_id"
    ]


    try:

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fields,
                extrasaction="ignore"
            )

            writer.writeheader()

            writer.writerows(
                attendance
            )


        messagebox.showinfo(
            "Export Successful",
            "Attendance exported successfully!\n\n"
            +
            file_path
        )


    except Exception as error:

        messagebox.showerror(
            "Export Error",
            str(error)
        )


# Export button

ctk.CTkButton(
    history_header,
    text="📥  Export",
    width=110,
    height=35,
    corner_radius=9,
    fg_color=PRIMARY,
    hover_color=PRIMARY_HOVER,
    text_color=WHITE,
    font=(FONT_BODY, 11, "bold"),
    command=export_attendance
).pack(
    side="right"
)


# =========================================================
# TABLE
# =========================================================

table_frame = ctk.CTkFrame(
    history_card,
    fg_color=WHITE
)

table_frame.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)


# Treeview style

style = ttk.Style()


try:

    style.theme_use(
        "clam"
    )

except Exception:

    pass


style.configure(
    "Attendance.Treeview",
    rowheight=32,
    font=(FONT_BODY, 10),
    background=WHITE,
    fieldbackground=WHITE,
    foreground=TEXT_COLOR
)


style.configure(
    "Attendance.Treeview.Heading",
    font=(FONT_BODY, 10, "bold"),
    background=PRIMARY,
    foreground=WHITE
)


style.map(
    "Attendance.Treeview",
    background=[
        (
            "selected",
            TINT
        )
    ],
    foreground=[
        (
            "selected",
            TEXT_COLOR
        )
    ]
)


columns = (

    "date",
    "time",
    "student",
    "subject",
    "status",
    "recognition"

)


tree = ttk.Treeview(

    table_frame,

    columns=columns,

    show="headings",

    style="Attendance.Treeview"
)


tree.heading(
    "date",
    text="Date"
)


tree.heading(
    "time",
    text="Time"
)


tree.heading(
    "student",
    text="Student"
)


tree.heading(
    "subject",
    text="Subject"
)


tree.heading(
    "status",
    text="Status"
)


tree.heading(
    "recognition",
    text="Recognition Result"
)


tree.column(
    "date",
    width=100,
    anchor="center"
)


tree.column(
    "time",
    width=90,
    anchor="center"
)


tree.column(
    "student",
    width=170
)


tree.column(
    "subject",
    width=120
)


tree.column(
    "status",
    width=100,
    anchor="center"
)


tree.column(
    "recognition",
    width=180,
    anchor="center"
)


scrollbar = ttk.Scrollbar(

    table_frame,

    orient="vertical",

    command=tree.yview
)


tree.configure(
    yscrollcommand=scrollbar.set
)


tree.pack(
    side="left",
    fill="both",
    expand=True
)


scrollbar.pack(
    side="right",
    fill="y"
)


# =========================================================
# UPDATE STUDENT PROFILE
# =========================================================

def update_student_profile(
    student
):

    global selected_student

    selected_student = student


    # Update text fields

    for key, label in profile_fields.items():

        value = student.get(
            key,
            "-"
        )

        label.configure(
            text=str(value)
        )


    profile_status.configure(
        text="✓ Student Selected",
        text_color=GREEN
    )


    # Student photo

    photo_path = student.get(
        "photo",
        ""
    )


    if photo_path:

        if not os.path.isabs(
            photo_path
        ):

            photo_path = os.path.join(
                BASE_DIR,
                photo_path
            )


    if (
        photo_path
        and
        os.path.exists(
            photo_path
        )
    ):

        try:

            image = Image.open(
                photo_path
            )


            image.thumbnail(
                (
                    210,
                    180
                )
            )


            photo = ctk.CTkImage(

                light_image=image,

                dark_image=image,

                size=image.size
            )


            profile_photo.configure(

                image=photo,

                text=""
            )


            profile_photo.image = photo


        except Exception:

            profile_photo.configure(

                image=None,

                text="Photo unavailable"
            )


    else:

        profile_photo.configure(

            image=None,

            text="📷\n\nPhoto unavailable"
        )


# =========================================================
# UPDATE SUMMARY
# =========================================================

def update_attendance_summary():

    if selected_student is None:

        summary_values[
            "total"
        ].configure(
            text="0"
        )

        summary_values[
            "present"
        ].configure(
            text="0"
        )

        summary_values[
            "absent"
        ].configure(
            text="0"
        )

        summary_values[
            "percentage"
        ].configure(
            text="0%"
        )

        return


    stats = ss.student_summary(
        selected_student.get(
            "student_id",
            ""
        )
    )

    total_days = stats["total"]

    present = stats["present"]

    absent = stats["absent"]

    percentage = stats["percentage"]


    summary_values[
        "total"
    ].configure(
        text=str(
            total_days
        )
    )


    summary_values[
        "present"
    ].configure(
        text=str(
            present
        )
    )


    summary_values[
        "absent"
    ].configure(
        text=str(
            absent
        )
    )


    summary_values[
        "percentage"
    ].configure(
        text=f"{percentage:.0f}%"
    )


# =========================================================
# UPDATE HISTORY
# =========================================================

def update_history():

    for item in tree.get_children():

        tree.delete(
            item
        )


    attendance = load_attendance()


    if selected_student:

        student_id = selected_student.get(
            "student_id",
            ""
        )

        attendance = [
            record
            for record in attendance
            if record.get("student_id") == student_id
        ]

    elif current_session:

        attendance = [
            record
            for record in attendance
            if record.get("session_id") == current_session["session_id"]
        ]

    else:

        attendance = [
            record
            for record in attendance
            if record.get("faculty_id", current_user["user_id"])
            == current_user["user_id"]
        ]


    # Newest first

    attendance = list(
        reversed(
            attendance
        )
    )


    for record in attendance:

        tree.insert(

            "",

            "end",

            values=(

                record.get(
                    "date",
                    "-"
                ),

                record.get(
                    "time",
                    "-"
                ),

                record.get(
                    "name",
                    "-"
                ),

                record.get(
                    "subject",
                    "-"
                ),

                record.get(
                    "status",
                    "-"
                ),

                record.get(
                    "recognition",
                    "-"
                )

            )
        )


# =========================================================
# SESSION FLOW
# =========================================================

def marked_count():

    if current_session is None:

        return 0

    return len(
        ss.session_attendance(
            current_session["session_id"]
        )
    )


def on_session_changed():

    global selected_student

    selected_student = None

    for label in profile_fields.values():

        label.configure(text="-")

    profile_status.configure(
        text="No Student Selected",
        text_color=MUTED_TEXT
    )

    profile_photo.configure(
        image=None,
        text="👤\n\nSelect Student"
    )

    session_bar.set_session(
        current_session,
        marked_count()
    )

    session_bar.refresh_others()

    update_attendance_summary()

    update_history()


def start_session_flow():

    global current_session

    if current_session is not None:

        return

    dialog = StartSessionDialog(
        app,
        load_students(),
        current_user
    )

    app.wait_window(dialog)

    if dialog.session:

        current_session = dialog.session

        on_session_changed()


def end_session_flow():

    global current_session

    if current_session is None:

        return

    total = len(current_session["student_ids"])

    if not messagebox.askyesno(
        "End Session",
        f"End '{current_session['subject']}' now?\n\n"
        f"{marked_count()} of {total} students marked. "
        "The students will be released for other faculty."
    ):

        return

    ss.end_session(
        current_session["session_id"]
    )

    current_session = None

    on_session_changed()


def select_from_roster(student):

    update_student_profile(
        student
    )

    update_attendance_summary()

    update_history()


def open_roster():

    if current_session is None:

        return

    RosterWindow(
        app,
        current_session,
        load_students(),
        select_from_roster
    )


def heartbeat_tick():

    global current_session

    try:

        if current_session is not None:

            if not ss.heartbeat(current_session["session_id"]):

                current_session = None

                messagebox.showwarning(
                    "Session Ended",
                    "Your session expired because it stopped "
                    "responding. Please start it again."
                )

                on_session_changed()

    except TimeoutError:

        pass

    app.after(
        ss.HEARTBEAT_EVERY * 1000,
        heartbeat_tick
    )


def refresh_tick():

    session_bar.refresh_others()

    if current_session is not None:

        session_bar.set_marked(
            marked_count()
        )

    app.after(
        3000,
        refresh_tick
    )


def shutdown():

    if current_session is not None:

        try:

            ss.end_session(
                current_session["session_id"]
            )

        except Exception:

            pass

    app.destroy()


app.protocol(
    "WM_DELETE_WINDOW",
    shutdown
)


# =========================================================
# ENTER KEY SEARCH
# =========================================================

search_entry.bind(
    "<Return>",
    lambda event: search_student()
)


# =========================================================
# INITIAL DATA
# =========================================================

students = load_students()


student_count_label.configure(
    text=f"Registered Students: {len(students)}"
)


update_attendance_summary()

update_history()


# =========================================================
# START APPLICATION
# =========================================================

session_bar.refresh_others()

app.after(
    ss.HEARTBEAT_EVERY * 1000,
    heartbeat_tick
)

app.after(
    3000,
    refresh_tick
)

print(
    "ATTENDANCE DASHBOARD IS RUNNING"
)


app.mainloop()