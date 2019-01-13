.. _tiger_leagues_views:

*****
Views
*****

As described on `Wikipedia 
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller#Components>`_, 
a view is any output representation of information.

.. _views_design_decisions:

Design Decisions
----------------

.. _uniform_design:

Uniform Design
^^^^^^^^^^^^^^

Our application has several pages, so it's important to keep their design 
uniform. Using the Jinja templates supported natively by Flask, we inherited 
templates whenever we felt that a group of pages should share some design.

.. _views_documentation:

Views Documentation
-------------------

base.html
^^^^^^^^^

Serves as the overall template for all other HTML files. The header and 
footer (and any other persistent content) should be added here.

error.html
^^^^^^^^^^

Used to render a custom error page.

admin/*
^^^^^^^

The HTML files found here correspond to different pages that are relevant to 
admins, e.g.

* ``admin_league_panel.html`` shows different actions that an admin can take
* ``approve_members.html`` and ``manage_members.html`` show pages for managing 
league members depending on whether the league is in progress or not.
* ``start_league.html`` allows the admin to allocate league divisions and 
generate fixtures.
* ``admin_league_homepage.html`` allows admins to approve pending scores.
* ``delete_league.html`` allows admins to delete the league.

auth/*
^^^^^^

Contains HTML files related to the authentication process, e.g.

* ``login.html`` provides a link to Princeton's Central Authentication System.

Since we're using Princeton's CAS, other auth-related pages such as resetting 
a password, validating an email address, etc, are not necessary.

league/*
^^^^^^^^

Contains HTML files related to a league from the viewpoint of a non-admin 
member.

* ``browse.html`` shows leagues that a user can request to join.
* ``create_league.html`` allows a user to create a new league.
* ``join_league.html`` allows a user to request to join an existing league.
* ``update_responses.html`` allows a user to update the responses that they 
had submitted to the league.
* ``league_base.html`` provides an inheritable template that has league header 
information at the top.
* ``league_homepage.html`` shows the current standings and upcoming matches of 
the logged in user.
* ``member_stats/league_comparison_base.html`` provides an inheritable 
template for displaying a player(s) stats within a league.
* ``member_stats/league_side_by_side_stats.html`` provides a side-by-side 
comparison of the logged in user and any other comparable player.
* ``member_stats/league_single_player_stats.html`` provides league stats for a 
single player (usually happens when user tries to view themselves, or a player 
who is not in the same division)

user/*
^^^^^^

Contains HTML files related to a user's account.

* ``user_profile.html`` allows a user to view and/or update their site-wide 
profile.
* ``user_notifications.html`` allows a user to read the notifications that 
have been sent to their mailbox.

