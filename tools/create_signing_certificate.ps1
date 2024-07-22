# This script creates a new self-signed certificate capable of signing our Windows executables and installer.

# Prompt the user for the password to encrypt the certificate with.
# This password is the WINDOWS_SIGNING_CERTIFICATE_PASSWORD secret.
$password = ConvertTo-SecureString -Force -AsPlainText

# Create a new certificate. It will be stored in the user certificate store, then exported to certificate.pfx
New-SelfSignedCertificate `
    -Type Custom `
    -Subject "CN=Randovania" `
    -KeyUsage DigitalSignature `
    -FriendlyName "Randovania" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    | Export-PfxCertificate -FilePath certificate.pfx -Password $password

certutil -encode .\certificate.pfx certificate.txt
# The contents of certificate.txt is the WINDOWS_SIGNING_CERTIFICATE secret
