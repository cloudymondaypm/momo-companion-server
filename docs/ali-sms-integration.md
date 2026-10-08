# Alibaba Cloud SMS Integration Guide

Open the [Alibaba Cloud SMS Console](https://dysms.console.aliyun.com/overview).

## Step 1: Add a signature

![Step](images/alisms/sms-01.png)
![Step](images/alisms/sms-02.png)

After creating the SMS signature, enter its value in the management console parameter `aliyun.sms.sign_name`.

## Step 2: Add an SMS template

![Step](images/alisms/sms-11.png)

Enter the template code in `aliyun.sms.sms_code_template_code` in the management console.

**Important:** Signature approval and carrier registration may take up to seven working days. Wait until approval is complete before sending SMS messages or continuing.

## Step 3: Create SMS credentials and grant access

Open the Alibaba Cloud [Resource Access Management console](https://ram.console.aliyun.com/overview?activeTab=overview).

![Step](images/alisms/sms-21.png)
![Step](images/alisms/sms-22.png)
![Step](images/alisms/sms-23.png)
![Step](images/alisms/sms-24.png)
![Step](images/alisms/sms-25.png)

Copy the credentials into `aliyun.sms.access_key_id` and `aliyun.sms.access_key_secret` in Parameter Management.

## Step 4: Enable phone registration

1. When all credentials and values are configured, your screen should resemble the example below. If not, review the previous steps.

   ![Step](images/alisms/sms-31.png)

2. To allow registration by non-administrators, set `server.allow_user_register` to `true`.
3. To enable phone-number registration, set `server.enable_mobile_register` to `true`.

   ![Step](images/alisms/sms-32.png)
