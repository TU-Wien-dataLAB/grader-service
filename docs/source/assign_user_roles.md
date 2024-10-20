# Assigning Users to Roles based on Authentication Info

Grader Service supports the `load_roles` config option to pre-load certain roles in the beginning.
However, this information should most likely be updated based on the authentication info received from the external authentication/authorization provider.
The achieve this, the `post_auth_hook` from the `Authenticator` class can be used to specify this behaviour.
In this case we are using the LTI 1.3 authenticator and map every user the has an instructor role defined by the IMS standard to Instructors in the Grader Service.

```python
def get_role_from_auth(auth_state):
user_role = 'student'
for role in auth_state['https://purl.imsglobal.org/spec/lti/claim/roles']:
    if role.find('Instructor') >= 1:
        user_role = 'instructor'
        break
return user_role


def post_auth_hook(authenticator: Authenticator, handler: BaseHandler, authentication: dict):
    print("####### POST AUTH HOOK")
    session = handler.session
    log = handler.log
    auth_state = authentication["auth_state"]

    username = authentication["name"]
    user_model: User = session.query(User).get(username)
    if user_model is None:
        user_model = User()
        user_model.name = username
        session.add(user_model)
        session.commit()

    lecture_code = auth_state["https://purl.imsglobal.org/spec/lti/claim/context"]["label"].replace(" ", "")
    lecture = session.query(Lecture).filter(Lecture.code == lecture_code).one_or_none()
    if lecture is None:
        lecture = Lecture()
        lecture.code = lecture_code
        lecture.name = lecture_code
        lecture.state = LectureState.active
        lecture.deleted = DeleteState.active
        session.add(lecture)
        session.commit()

    lti_role = get_role_from_auth(auth_state)
    scope = Scope[lti_role.lower()]
    log.info(f'Determined role {scope.name} for user {username}')

    role = session.query(Role).filter(Role.username == username, Role.lectid == lecture.id).one_or_none()
    if role is None:
        log.info(f'No role for user {username} in lecture {lecture_code}... creating role')
        role = Role(username=username, lectid=lecture.id, role=scope)
        session.add(role)
        session.commit()
    else:
        log.info(f'Found role {role.role.name} for user {username}  in lecture {lecture_code}... updating role to {scope.name}')
        role.role = scope
        session.commit()

    return authentication


c.Authenticator.post_auth_hook = post_auth_hook
```