import os

# Define the keys as clean single-line strings with literal \n
private_key = r"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDD2NiUzBvoW/Bn\ntRWlRj+TROWjzoEA3b4jyQPKRYGXQIo9ipLLAzI1G0VFbXdj4cKz7jajp4siwK/f\nAjmDmDR+lPvDXv/bzqSidNGVDUVH9NFd2PJqQMVeTaYFfmtqVI5TkynP0E302f87\nXdtqO0bDVz5q20PXzmknqI/2zzMnOrLyv2PD4CLsb9tL0DrdEEgAWEmcpD4PR5Jl\n4hD99d0OMmAi+8YAidgA4y25ddS4JrYmKn/2dJv4CnG4RLuqY7D6+Jk8Qb1tCaT5\nbVPakUk5ZR9bUp7F1Tm5AdDZP97XcL7a8nz2YkvSzb0WbAUPyEgRVtGcTxHYH4Mg\nZNv6g8bzAgMBAAECggEAHZI29ZSyHA4RyR7zEz79p3duMyMhoGda591YuKhxDkz8\n8pjjXErxwEoLVhXWwpqagv+TeXd5TziH9aTI2WFYf8pwD0pfWKmlezAnWxmjXd+N\n4104ESoRgxE3Ybn6bxYwXVcpp4q80p096BFeaXZk02bvckQEROgSQZ42ip4zi5cS\nBChGDWPJREgJv37XFHECV0dMLNokjKdJeu86YrMRu1f6ruER2gNRoGoVOiwzq/9P\nRYVqDW/u9w0MQCmTvYpRfqZR8Vm4Enp/mwvnCmZdDm6ite/e59CYeNddwLwiGPhq\nOZvGf7zSrVGLEimM9dt/YgotTU0LrKWYGxdAJdgVAQKBgQDzxP3q1SCX/3maCpsj\niGPS9wbXXhhZu3IFN1Gm6DnBUwBxJIZUJqyU09Aa7dHZJD2/c+Iz0aiRiTE7h7I\nxBjlVHcvKvoYDBoFlpnPidZm+F5KYSEbunXDdGEwlbkytxjglwbdY4bfXo+eJOLa\npHJD1PoxfG8aNEuoHxGqPpId8wKBgQDNrFT0LLmMtXzvZmtqpQBsJbCsO0G2RXPg\niItE7w4Gv8+JkCEJn9NR7FjIoDiI5cQMNDL7HXPke0wnDCXfrMSXmaB7cq1ypEzy\nnBpcTI3vahP1Gz2cQBIde5E7Eb3VEEBmFYJNaLtcDHH0eNWl8IsilKsvVJOjNQSW\ns+LEvWzzAQKBgQDFLKf+FNpCWADyGnYWP0gB8mhdMiO3FVxsJIQ/Io7pjp1GKMvL\n8ijO6RgHkZk0BCJFxlLh5FbL11TSfZEk74j7pnCpFGgqn09FCeXruyBTNb5/B0WS\neiXbLP2YIOMmJHfY4hBJbsGfV4tvbYKZO765I0IkWPQ9C+POXyMYw3fJBQKBgAmM\vekUho0NBD8Nb2FlRe6/lUN6AOQYt3euf2D1BJ61m0pU4ePTgvlj0v+FyPo6SO8U\nIWXdiTsLqo6Jltya5gnv/S6eNYWEMXp2Wxb8Cv8Z2tFfsW2m3/B0g1rNyRWyinry\n9rjnawOsJEJoterdj2hMpOIuuCg01wC0W4wtC3kBAoGBANDR3lqU/AlOh8+kQ6FM\nyqa2evcYSqGugPWBSD2h9LucKpSWwggpNlZoySEDiNnyBU4R3ecXT4TsIQ5VlW2G\npfX0lQy1QTLHCdEYY8EcDD6D5ecUN8Lu6yKz1+7fN4onO0zciv3PfIEqz+rMM2tF\n1fPen7Ku7R7JRt8xfdHFfnq5\n-----END PRIVATE KEY-----\n"

public_key = r"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAw9jYlMwb6FvwZ7UVpUY/\nk0Tlo86BAN2+I8kDykWBl0CKPYqSywMyNRtFRW13Y+HCs+42o6eLIsCv3wI5g5g0\nfpT7w17/286konTRlQ1FR/TRXdjyakDFXk2mBX5ralSOU5Mpz9BN9Nn/O13bajtG\nw1c+attD185pJ6iP9s8zJzqy8r9jw+Ai7G/bS9A63RBIAFhJnKQ+D0eSZeIQ/fXd\nDjJgIvvGAInYAOMtuXXUuCa2Jip/9nSb+ApxuES7qmOw+viZPEG9bQmk+W1T2pFJ\nOWUfW1KexdU5uQHQ2T/e13C+2vJ89mJL0s29FmwFD8hIEVbRnE8R2B+DIGTb+oPG\n8wIDAQAB\n-----END PUBLIC KEY-----\n"

# Read .env
with open(".env", "r") as f:
    lines = f.readlines()

# Update lines
with open(".env", "w") as f:
    for line in lines:
        if line.startswith("JWT_PRIVATE_KEY="):
            f.write(f'JWT_PRIVATE_KEY="{private_key}"\n')
        elif line.startswith("JWT_PUBLIC_KEY="):
            f.write(f'JWT_PUBLIC_KEY="{public_key}"\n')
        else:
            f.write(line)

print("SUCCESS: Quoted single-line JWT keys written to .env")
