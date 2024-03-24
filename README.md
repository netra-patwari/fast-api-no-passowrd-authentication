
----------
----------
### API Reference



#### Login

```http
  POST /auth/login
```

| Request body  | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `email` | `string` | **Required**. Checks wheather email in DB or not. If user it sends OTP on email|

#### Response


```json
{
"user_validation_id": "unique_user_validation_id"
}
```
If user not in db than user_validation_id  will be null

---

#### Create User

Create user if login api returns user_validation_id null
```http
  POST /auth/create-user
```

| Request body  | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `email` | `string` | **Required**. Creates a user entry, if new email and sends OTP |

#### Response

```json
{
"user_validation_id": "unique_user_validation_id"
}
```



#### Validate OTP

```http
  POST /auth/validate_otp
```

| Request body  | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `otp` | `string` | **Required**. One-Time Password sent to the user's email. |
| `user_validation_id` | `string` | **Required**. Unique user validation ID obtained during create user. |

#### Response

```json
{
  "access_token": "user_access_token",
  "is_registered": false # if new user 
}

```
---



#### Resend OTP

Sends new OTP 

```http
  POST /auth/resend_otp
```

| Request body  | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `user_validation_id` | `string` | **Required**. Unique user validation ID obtained during create user. |

#### Response

```json
{
  "user_validation_id": "unique_user_validation_id"
}


```


---




#### Register


```http
  POST /auth/resend_otp
```

| Request body  | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `first_name` | `string` | **Required**. User's first name. |
| `last_name` | `string` | **Required**. User's last name. |
| `profile_photo` | `string` | **Required**. Base64 format url |
| `country_code` | `string` | **Required**. country_code |
| `phone_no` | `string` | **Required**. 10 digit number |
| `email` | `string` | **Required**. user email. |



#### Response

```json
{
  "access_token": "unique_access_token"
}


```

