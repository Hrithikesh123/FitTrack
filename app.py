
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)

# Secret key for login sessions
app.secret_key = "fittrack-secret-key"

DATABASE = "fittrack.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# LOGIN CHECK
# =========================================================

def logged_in():
    return "user_id" in session


# =========================================================
# CALCULATE BEST STREAK
# =========================================================

def calculate_best_streak(user_id):

    connection = get_db_connection()

    all_goals = connection.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    completed_dates = []

    unique_dates = []

    # Get all unique goal dates
    for goal in all_goals:

        if goal["date"] not in unique_dates:

            unique_dates.append(
                goal["date"]
            )

    # Check which days had all goals completed
    for current_date in unique_dates:

        day_goals = []

        for goal in all_goals:

            if goal["date"] == current_date:

                day_goals.append(goal)

        all_completed = True

        for goal in day_goals:

            if not goal["completed"]:

                all_completed = False

                break

        if all_completed:

            completed_dates.append(
                current_date
            )

    # Calculate best streak
    best_streak = 0

    streak = 0

    sorted_dates = sorted(
        completed_dates
    )

    for i in range(
        len(sorted_dates)
    ):

        if i == 0:

            streak = 1

        else:

            previous_date = date.fromisoformat(
                sorted_dates[i - 1]
            )

            current_date = date.fromisoformat(
                sorted_dates[i]
            )

            if (
                current_date
                - previous_date
                == timedelta(days=1)
            ):

                streak += 1

            else:

                streak = 1

        if streak > best_streak:

            best_streak = streak

    return best_streak


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (
                username,
                password
            )
        ).fetchone()

        connection.close()

        if user:

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template(
        "login.html"
    )


# =========================================================
# REGISTER PAGE
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        connection = get_db_connection()

        try:

            connection.execute(
                """
                INSERT INTO users
                (username, password)

                VALUES (?, ?)
                """,
                (
                    username,
                    password
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Username already exists."
            )

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        connection.close()

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        return redirect("/")

    return render_template(
        "register.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    if request.method == "POST":

        username = request.form["username"]

        new_password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if user:

            connection.execute(
                """
                UPDATE users

                SET password = ?

                WHERE username = ?
                """,
                (
                    new_password,
                    username
                )
            )

            connection.commit()

            connection.close()

            return redirect("/login")

        connection.close()

        return render_template(
            "reset_password.html",
            error="Username not found."
        )

    return render_template(
        "reset_password.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# DASHBOARD
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    today = str(
        date.today()
    )

    connection = get_db_connection()

    # -------------------------
    # ADD NEW GOAL
    # -------------------------

    if request.method == "POST":

        goal_text = request.form["goal"]

        connection.execute(
            """
            INSERT INTO goals
            (
                user_id,
                goal,
                completed,
                date
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                goal_text,
                0,
                today
            )
        )

        connection.commit()

        connection.close()

        return redirect("/")

    # -------------------------
    # TODAY'S GOALS
    # -------------------------

    today_goals = connection.execute(
        """
        SELECT *
        FROM goals

        WHERE user_id = ?

        AND date = ?

        ORDER BY id
        """,
        (
            user_id,
            today
        )
    ).fetchall()

    # -------------------------
    # GOAL PROGRESS
    # -------------------------

    completed_goals = 0

    for goal in today_goals:

        if goal["completed"]:

            completed_goals += 1

    total_goals = len(
        today_goals
    )

    if total_goals > 0:

        progress = round(
            (
                completed_goals
                / total_goals
            ) * 100
        )

    else:

        progress = 0

    # -------------------------
    # WORKOUT STATISTICS
    # -------------------------

    workouts = connection.execute(
        """
        SELECT *
        FROM workouts

        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchall()

    total_exercises = len(
        workouts
    )

    completed_exercises = 0

    for exercise in workouts:

        if exercise["completed"]:

            completed_exercises += 1

    # -------------------------
    # WORKOUT CATEGORIES
    # -------------------------

    category_counts = {

        "Strength": 0,

        "Cardio": 0,

        "Flexibility": 0,

        "HIIT": 0

    }

    for exercise in workouts:

        category = exercise["category"]

        if category in category_counts:

            category_counts[
                category
            ] += 1

    connection.close()

    # -------------------------
    # BEST STREAK
    # -------------------------

    best_streak = calculate_best_streak(
        user_id
    )

    # -------------------------
    # SEND DATA TO DASHBOARD
    # -------------------------

    return render_template(

        "index.html",

        goals=today_goals,

        progress=progress,

        best_streak=best_streak,

        total_exercises=total_exercises,

        completed_exercises=completed_exercises,

        category_counts=category_counts,

        username=session["username"]

    )


# =========================================================
# COMPLETE GOAL
# =========================================================

@app.route(
    "/complete/<int:goal_index>"
)
def complete_goal(goal_index):

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    today = str(
        date.today()
    )

    today_goals = connection.execute(
        """
        SELECT *
        FROM goals

        WHERE user_id = ?

        AND date = ?

        ORDER BY id
        """,
        (
            user_id,
            today
        )
    ).fetchall()

    if (
        0 <= goal_index
        < len(today_goals)
    ):

        goal_id = today_goals[
            goal_index
        ]["id"]

        connection.execute(
            """
            UPDATE goals

            SET completed = 1

            WHERE id = ?

            AND user_id = ?
            """,
            (
                goal_id,
                user_id
            )
        )

        connection.commit()

    connection.close()

    return redirect("/")


# =========================================================
# DELETE GOAL
# =========================================================

@app.route(
    "/delete-goal/<int:goal_index>"
)
def delete_goal(goal_index):

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    goals = connection.execute(
        """
        SELECT *
        FROM goals

        WHERE user_id = ?

        ORDER BY date DESC, id
        """,
        (user_id,)
    ).fetchall()

    if (
        0 <= goal_index
        < len(goals)
    ):

        goal_id = goals[
            goal_index
        ]["id"]

        connection.execute(
            """
            DELETE FROM goals

            WHERE id = ?

            AND user_id = ?
            """,
            (
                goal_id,
                user_id
            )
        )

        connection.commit()

    connection.close()

    return redirect("/goals")


# =========================================================
# EDIT GOAL
# =========================================================

@app.route(
    "/edit-goal/<int:goal_index>",
    methods=["GET", "POST"]
)
def edit_goal(goal_index):

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    goals = connection.execute(
        """
        SELECT *
        FROM goals

        WHERE user_id = ?

        ORDER BY date DESC, id
        """,
        (user_id,)
    ).fetchall()

    if (
        goal_index < 0
        or goal_index >= len(goals)
    ):

        connection.close()

        return redirect("/goals")

    goal = goals[
        goal_index
    ]

    if request.method == "POST":

        new_goal = request.form[
            "goal"
        ]

        connection.execute(
            """
            UPDATE goals

            SET goal = ?

            WHERE id = ?

            AND user_id = ?
            """,
            (
                new_goal,
                goal["id"],
                user_id
            )
        )

        connection.commit()

        connection.close()

        return redirect("/goals")

    connection.close()

    return render_template(

        "edit_goal.html",

        goal=goal,

        goal_index=goal_index

    )


# =========================================================
# WORKOUTS
# =========================================================

@app.route(
    "/workouts",
    methods=["GET", "POST"]
)
def workouts():

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    if request.method == "POST":

        connection.execute(
            """
            INSERT INTO workouts
            (
                user_id,
                exercise,
                sets,
                reps,
                category,
                completed
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                request.form["exercise"],
                request.form["sets"],
                request.form["reps"],
                request.form["category"],
                0
            )
        )

        connection.commit()

        connection.close()

        return redirect("/workouts")

    workout = connection.execute(
        """
        SELECT *
        FROM workouts

        WHERE user_id = ?

        ORDER BY id
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(

        "workouts.html",

        workout=workout

    )


# =========================================================
# COMPLETE EXERCISE
# =========================================================

@app.route(
    "/complete-exercise/<int:exercise_index>"
)
def complete_exercise(
    exercise_index
):

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    workout = connection.execute(
        """
        SELECT *
        FROM workouts

        WHERE user_id = ?

        ORDER BY id
        """,
        (user_id,)
    ).fetchall()

    if (
        0 <= exercise_index
        < len(workout)
    ):

        exercise_id = workout[
            exercise_index
        ]["id"]

        connection.execute(
            """
            UPDATE workouts

            SET completed = 1

            WHERE id = ?

            AND user_id = ?
            """,
            (
                exercise_id,
                user_id
            )
        )

        connection.commit()

    connection.close()

    return redirect(
        "/workouts"
    )


# =========================================================
# DELETE EXERCISE
# =========================================================

@app.route(
    "/delete-exercise/<int:exercise_index>"
)
def delete_exercise(
    exercise_index
):

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    workout = connection.execute(
        """
        SELECT *
        FROM workouts

        WHERE user_id = ?

        ORDER BY id
        """,
        (user_id,)
    ).fetchall()

    if (
        0 <= exercise_index
        < len(workout)
    ):

        exercise_id = workout[
            exercise_index
        ]["id"]

        connection.execute(
            """
            DELETE FROM workouts

            WHERE id = ?

            AND user_id = ?
            """,
            (
                exercise_id,
                user_id
            )
        )

        connection.commit()

    connection.close()

    return redirect(
        "/workouts"
    )


# =========================================================
# EDIT EXERCISE
# =========================================================

@app.route(
    "/edit-exercise/<int:exercise_index>",
    methods=["GET", "POST"]
)
def edit_exercise(
    exercise_index
):

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    workout = connection.execute(
        """
        SELECT *
        FROM workouts

        WHERE user_id = ?

        ORDER BY id
        """,
        (user_id,)
    ).fetchall()

    if (
        exercise_index < 0
        or exercise_index >= len(workout)
    ):

        connection.close()

        return redirect(
            "/workouts"
        )

    exercise = workout[
        exercise_index
    ]

    if request.method == "POST":

        connection.execute(
            """
            UPDATE workouts

            SET exercise = ?,
                sets = ?,
                reps = ?,
                category = ?

            WHERE id = ?

            AND user_id = ?
            """,
            (
                request.form["exercise"],
                request.form["sets"],
                request.form["reps"],
                request.form["category"],
                exercise["id"],
                user_id
            )
        )

        connection.commit()

        connection.close()

        return redirect(
            "/workouts"
        )

    connection.close()

    return render_template(

        "edit_exercise.html",

        exercise=exercise,

        exercise_index=exercise_index

    )


# =========================================================
# GOALS PAGE
# =========================================================

@app.route(
    "/goals",
    methods=["GET", "POST"]
)
def goals():

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    if request.method == "POST":

        connection.execute(
            """
            INSERT INTO goals
            (
                user_id,
                goal,
                completed,
                date
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                request.form["goal"],
                0,
                str(date.today())
            )
        )

        connection.commit()

        connection.close()

        return redirect(
            "/goals"
        )

    goals = connection.execute(
        """
        SELECT *
        FROM goals

        WHERE user_id = ?

        ORDER BY date DESC, id
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(

        "goals.html",

        goals=goals

    )


# =========================================================
# PROGRESS PAGE
# =========================================================

@app.route("/progress")
def progress_page():

    if not logged_in():

        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()

    today = date.today()

    start_of_week = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    # -------------------------
    # GET USER GOALS
    # -------------------------

    all_goals = connection.execute(
        """
        SELECT *
        FROM goals

        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchall()

    # -------------------------
    # WEEKLY GOALS
    # -------------------------

    weekly_goals = []

    for goal in all_goals:

        goal_date = date.fromisoformat(
            goal["date"]
        )

        if (
            start_of_week
            <= goal_date
            <= today
        ):

            weekly_goals.append(
                goal
            )

    completed_goals = 0

    for goal in weekly_goals:

        if goal["completed"]:

            completed_goals += 1

    # -------------------------
    # USER WORKOUTS
    # -------------------------

    workouts = connection.execute(
        """
        SELECT *
        FROM workouts

        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchall()

    completed_exercises = 0

    for exercise in workouts:

        if exercise["completed"]:

            completed_exercises += 1

    total_exercises = len(
        workouts
    )

    # -------------------------
    # CATEGORY COUNTS
    # -------------------------

    category_counts = {

        "Strength": 0,

        "Cardio": 0,

        "Flexibility": 0,

        "HIIT": 0

    }

    for exercise in workouts:

        category = exercise[
            "category"
        ]

        if category in category_counts:

            category_counts[
                category
            ] += 1

    # -------------------------
    # WEEKLY PROGRESS
    # -------------------------

    weekly_progress = []

    for i in range(7):

        current_day = (

            start_of_week

            + timedelta(
                days=i
            )

        )

        day_goals = []

        for goal in all_goals:

            if (
                goal["date"]
                == str(current_day)
            ):

                day_goals.append(
                    goal
                )

        if len(day_goals) == 0:

            daily_progress = 0

        else:

            completed = 0

            for goal in day_goals:

                if goal["completed"]:

                    completed += 1

            daily_progress = round(

                completed
                / len(day_goals)
                * 100

            )

        weekly_progress.append({

            "date":
                current_day.strftime(
                    "%a"
                ),

            "progress":
                daily_progress

        })

    # -------------------------
    # CURRENT STREAK
    # -------------------------

    completed_dates = []

    unique_dates = []

    for goal in all_goals:

        if (
            goal["date"]
            not in unique_dates
        ):

            unique_dates.append(
                goal["date"]
            )

    for current_date in unique_dates:

        day_goals = []

        for goal in all_goals:

            if (
                goal["date"]
                == current_date
            ):

                day_goals.append(
                    goal
                )

        all_completed = True

        for goal in day_goals:

            if not goal["completed"]:

                all_completed = False

                break

        if all_completed:

            completed_dates.append(
                current_date
            )

    current_streak = 0

    check_date = today

    while (
        str(check_date)
        in completed_dates
    ):

        current_streak += 1

        check_date -= timedelta(
            days=1
        )

    # -------------------------
    # BEST STREAK
    # -------------------------

    best_streak = calculate_best_streak(
        user_id
    )

    connection.close()

    # -------------------------
    # SEND DATA TO PROGRESS PAGE
    # -------------------------

    return render_template(

        "progress.html",

        completed_goals=
            completed_goals,

        completed_exercises=
            completed_exercises,

        total_exercises=
            total_exercises,

        current_streak=
            current_streak,

        best_streak=
            best_streak,

        weekly_total=
            len(weekly_goals),

        weekly_progress=
            weekly_progress,

        category_counts=
            category_counts

    )


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )

