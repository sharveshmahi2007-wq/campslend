package com.campuslend.service;

import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
public class EmailService {

    private static final Logger log = LoggerFactory.getLogger(EmailService.class);

    private final JavaMailSender mailSender;

    @Value("${spring.mail.username:}")
    private String fromEmail;

    @Autowired(required = false)
    public EmailService(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    /**
     * Sends a 6-digit OTP verification email to the student's official @psgitech.ac.in address.
     * If SMTP is not yet configured or fails, it gracefully logs the OTP to console for local testing.
     */
    public boolean sendOtpEmail(String toEmail, String otpCode) {
        String subject = "Your PSG iTech Campus Lend Verification Code: " + otpCode;
        String htmlContent = buildOtpHtmlTemplate(toEmail, otpCode);

        // Always log for local development & diagnostics
        log.info("=====================================================================");
        log.info(" [PSG iTech Email Service] Sending OTP to: {}", toEmail);
        log.info(" [PSG iTech Email Service] OTP Code: {} (Expires in 5 minutes)", otpCode);
        log.info("=====================================================================");

        if (mailSender == null || fromEmail == null || fromEmail.isBlank()) {
            log.warn("[EmailService] SMTP credentials not set (SPRING_MAIL_USERNAME). Simulating email dispatch to console.");
            return true;
        }

        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setFrom(fromEmail, "PSG iTech Campus Lend");
            helper.setTo(toEmail);
            helper.setSubject(subject);
            helper.setText(htmlContent, true);

            mailSender.send(message);
            log.info("[EmailService] OTP email successfully dispatched via SMTP to {}", toEmail);
            return true;
        } catch (Exception e) {
            log.error("[EmailService] Failed to send email via SMTP (will continue with logged OTP): {}", e.getMessage());
            // Return true so developer testing isn't blocked when testing offline
            return true;
        }
    }

    private String buildOtpHtmlTemplate(String studentEmail, String otp) {
        return "<!DOCTYPE html>"
                + "<html>"
                + "<head><meta charset='UTF-8'></head>"
                + "<body style='font-family: Arial, sans-serif; background-color: #f8faff; margin: 0; padding: 24px; color: #071c3d;'>"
                + "  <div style='max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e8edff; padding: 32px; box-shadow: 0 4px 20px rgba(0,39,83,0.06);'>"
                + "    <div style='text-align: center; margin-bottom: 24px;'>"
                + "      <div style='display: inline-block; background: #002753; color: #ffffff; padding: 8px 16px; border-radius: 10px; font-weight: bold; font-size: 16px; letter-spacing: 0.5px;'>"
                + "        PSG iTech Campus Lend"
                + "      </div>"
                + "      <p style='color: #0051d5; font-size: 12px; font-weight: 600; margin-top: 6px; text-transform: uppercase; letter-spacing: 1px;'>"
                + "        PSG Institute of Technology and Applied Research"
                + "      </p>"
                + "    </div>"
                + "    <h2 style='color: #002753; font-size: 20px; font-weight: bold; margin-bottom: 12px; text-align: center;'>"
                + "      Verify Your Official College Email"
                + "    </h2>"
                + "    <p style='color: #495057; font-size: 14px; line-height: 1.6; text-align: center; margin-bottom: 24px;'>"
                + "      Hello PSG iTech Student,<br>"
                + "      Use the 6-digit one-time password (OTP) below to authenticate your student account for <strong>" + studentEmail + "</strong>."
                + "    </p>"
                + "    <div style='background: #f1f4fd; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; border: 1px dashed #0051d5;'>"
                + "      <span style='font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #002753; display: block; font-family: monospace;'>"
                + otp
                + "      </span>"
                + "      <span style='color: #ba1a1a; font-size: 12px; font-weight: bold; display: block; margin-top: 8px;'>"
                + "        ⏱ Valid for 5 minutes only • Single use"
                + "      </span>"
                + "    </div>"
                + "    <ul style='color: #6c757d; font-size: 12px; line-height: 1.5; padding-left: 18px; margin-bottom: 24px;'>"
                + "      <li>This verification ensures exclusive access for verified PSG iTech students.</li>"
                + "      <li>Do not share this OTP with anyone, including campus ambassadors.</li>"
                + "      <li>Maximum 5 verification attempts allowed.</li>"
                + "    </ul>"
                + "    <hr style='border: none; border-top: 1px solid #e8edff; margin: 24px 0;'>"
                + "    <p style='color: #adb5bd; font-size: 11px; text-align: center; margin: 0;'>"
                + "      PSG Institute of Technology and Applied Research • Neelambur, Coimbatore<br>"
                + "      LendLoop Peer-to-Peer Campus Marketplace"
                + "    </p>"
                + "  </div>"
                + "</body>"
                + "</html>";
    }
}

