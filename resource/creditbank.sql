-- phpMyAdmin SQL Dump
-- version 4.7.4
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 20, 2025 at 07:53 PM
-- Server version: 10.1.29-MariaDB
-- PHP Version: 7.2.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `creditbank`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int(11) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `username` varchar(10) NOT NULL,
  `gender` enum('Male','Female') NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin') NOT NULL,
  `tel` varchar(20) NOT NULL,
  `profile_image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`id`, `first_name`, `last_name`, `email`, `username`, `gender`, `password`, `role`, `tel`, `profile_image`) VALUES
(3, 'admin', 'teste', 'admin@gmail.com', 'admin', 'Male', 'scrypt:32768:8:1$vkJUSWAzx0Vsmj98$0ca7495f5c23fb3065e2258f3087160b9dfb8167b0596a3ba664f7dd4f87953e799eada96e4022b91232aac0cba897fa05c4644da9f826d63a3879cce47f0d8d', 'admin', '0987676774', '3_20250731011939_gg.png'),
(7, 'supap', 'rukdee', 'asdadasd@gmail.com', 'tests1234', 'Male', 'scrypt:32768:8:1$twRmfoNf9zTyjogk$30ba73f74e0b685b6ba47cc895c1b8c12b80a97b6ac6cb94b8e212600f39e9340c3e3b6055b9e3d2904995ac73a4c869bb3e4b94e20fdf6c833bd0dfef6c3b57', 'admin', '0944334455', NULL),
(8, 'su', 'po', 'zxcv@gmail.com', 'love', 'Male', 'scrypt:32768:8:1$ZJuSev8p1yvAUQ5O$ad88dfeda7fbaf6414f300293f8a56aba682304af4a4c716871cf456d34a2798cf1e24fd00e19c6d4e53407c3c0e15a6cd64e646d886f3e98dc5a91577f0e26e', 'admin', '0987654321', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE `categories` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `categories`
--

INSERT INTO `categories` (`id`, `name`) VALUES
(1, 'cybersecurity');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `id` int(11) NOT NULL,
  `featured_image` varchar(255) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `instructor_id` int(11) DEFAULT NULL,
  `categories_id` int(11) DEFAULT NULL,
  `description` text,
  `status` enum('publish','draft') NOT NULL DEFAULT 'draft',
  `featured_video` varchar(300) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`id`, `featured_image`, `title`, `created_at`, `instructor_id`, `categories_id`, `description`, `status`, `featured_video`) VALUES
(12, '12_20250804094252_course.jpg', 'Information Systems Security', '2025-06-16 19:00:01', 6, 1, 'รายวิชา Information Systems Security ศึกษาเกี่ยวกับหลักการ แนวคิด เทคนิค และเครื่องมือต่าง ๆ ที่ใช้ในการรักษาความมั่นคงปลอดภัยของระบบสารสนเทศ ครอบคลุมการป้องกันข้อมูล การจัดการความเสี่ยง การเข้ารหัส การพิสูจน์ตัวตน การควบคุมการเข้าถึง ตลอดจนการตรวจสอบและตอบสนองต่อเหตุการณ์ด้านความมั่นคง เพื่อให้ระบบสารสนเทศมีความปลอดภัยจากการโจมตี การบุกรุก หรือความเสียหายที่อาจเกิดขึ้น', 'publish', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `course_completions`
--

CREATE TABLE `course_completions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `completion_date` date NOT NULL,
  `certificate_code` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `course_completions`
--

INSERT INTO `course_completions` (`id`, `user_id`, `course_id`, `completion_date`, `certificate_code`) VALUES
(1, 34, 12, '2025-08-13', 'CERT-12-34-1755089115');

-- --------------------------------------------------------

--
-- Table structure for table `instructor`
--

CREATE TABLE `instructor` (
  `id` int(11) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `username` varchar(10) NOT NULL,
  `gender` enum('Male','Female') NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('instructor') NOT NULL,
  `tel` varchar(20) NOT NULL,
  `profile_image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `instructor`
--

INSERT INTO `instructor` (`id`, `first_name`, `last_name`, `email`, `username`, `gender`, `password`, `role`, `tel`, `profile_image`) VALUES
(6, 'jamjann', 'mungpijit', 'instructor@gmail.com', 'instructor', 'Female', 'scrypt:32768:8:1$zBTKTEERcHaUHLtz$138f13bcafffe559ac5c294ffa493f010e93b3294351e8b48ee76910a2f58afc555df4ae45e2dc50ae9ee7b69e5fecb8cb79c3b590d4708e65ad93572a9d7ffc', 'instructor', '0944334433', '6_20250807145903_kk.png'),
(7, 'lao', 'ty', 'twfsdfdd@gmail.com', 'test2', 'Female', 'scrypt:32768:8:1$BJZDSC4sBWip9fRo$6065696a9106fc04616baade252d53717f96e929c9f56ffa94db76af067ff61309426bc823cf653b25297cf689654df05079bada812502ab2531efa2150fca6b', 'instructor', '0944334778', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `lesson`
--

CREATE TABLE `lesson` (
  `lesson_id` int(11) NOT NULL,
  `lesson_name` varchar(255) NOT NULL,
  `lesson_date` datetime NOT NULL,
  `course_id` int(11) NOT NULL,
  `instructor_id` int(11) NOT NULL,
  `description` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `lesson`
--

INSERT INTO `lesson` (`lesson_id`, `lesson_name`, `lesson_date`, `course_id`, `instructor_id`, `description`) VALUES
(6, 'หน่วยที่ 1 แบบทดสอบพื้นฐานความมั่นคงของระบบสารสนเทศ', '2025-06-16 00:00:00', 12, 6, NULL),
(7, 'หน่วยที่ 2 วงจรการพัฒนาระบบความมั่นคงของระบบสารสนเทศ', '2025-07-21 00:00:00', 12, 6, NULL),
(8, 'หน่วยที่ 3 วิธีการและเทคนิครักษาความมั่นคงของระบบสารสนเทศ', '2025-07-24 00:00:00', 12, 6, NULL),
(9, 'หน่วยที่ 4 นโยบายในการสร้างความมั่นคงของระบบสารสนเทศ', '2025-07-31 00:00:00', 12, 6, NULL),
(11, 'หน่วยที่ 5 กลไกในการสร้างความปลอดภัยและเครื่องมือช่วยใน การสร้างมั่นคงของระบบสารสนเทศ', '2025-07-31 00:00:00', 12, 6, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `questions`
--

CREATE TABLE `questions` (
  `question_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `score` int(11) NOT NULL,
  `question_name` varchar(255) NOT NULL,
  `choice_a` varchar(255) NOT NULL,
  `choice_b` varchar(255) NOT NULL,
  `choice_c` varchar(255) NOT NULL,
  `choice_d` varchar(255) NOT NULL,
  `correct_answer` enum('a','b','c','d') NOT NULL,
  `question_image` varchar(255) NOT NULL,
  `choice_a_image` varchar(255) NOT NULL,
  `choice_b_image` varchar(255) NOT NULL,
  `choice_c_image` varchar(255) NOT NULL,
  `choice_d_image` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `questions`
--

INSERT INTO `questions` (`question_id`, `quiz_id`, `score`, `question_name`, `choice_a`, `choice_b`, `choice_c`, `choice_d`, `correct_answer`, `question_image`, `choice_a_image`, `choice_b_image`, `choice_c_image`, `choice_d_image`) VALUES
(19, 42, 1, '1. ข้อใดคือองค์ประกอบของความมั ่นคงสารสนเทศ (CIA Triad)?', 'Control, Integrity, Accuracy ', 'Confidentiality, Integrity, Availability', 'Communication, Innovation, Access ', ' Compliance, Information, Audit ', 'b', '', '', '', '', ''),
(20, 42, 1, '2. ข้อใดอธิบายคำว่า Threat ได้ถูกต้องที่สุด? ', ' ช่องโหว่ในระบบ', 'วิธีการที่ใช้ป้องกันข้อมูล', ' ความเสี่ยงทางการเงิน', 'สงทที่อาจก่อให้เกิดอันตรายต่อระบบ ', 'd', '', '', '', '', ''),
(21, 43, 1, '5. ข้อใดไม่ใช่ประเภทของ Security Control?', ' Physical Control', 'Administrative Control', 'Technical Control', ' Financial Control', 'd', '', '', '', '', ''),
(22, 43, 1, '6. Firewall ท าหน้าที่อะไร?', ' ตรวจสอบความเร็วอินเทอร์เน็ต', ' ป้องกันการเข้าถึงเครือข่ายโดยไม่ได้รับอนุญาต', ' เขา้รหสัขอ้มูลท้งัหมด', ' บันทึกการใช้งานเว็บไซต', 'b', '', '', '', '', ''),
(23, 43, 1, '7. ข้อใดคือความแตกต่างหลักระหว่าง IDS และ IPS?', 'IDS ป้องกันไวรัส, IPS ตรวจสอบอินเทอร์เน็ต', 'IDS ตรวจจับ, IPS ป้องกัน', 'IDS เก็บข้อมูล, IPS สร้างรหัสผ่าน', 'IDS คือฮาร์ดแวร์, IPS คือซอฟต์แวร', 'b', '', '', '', '', ''),
(24, 43, 1, '8. Public Key ใช้ทำอะไร?', 'ถอดรหัสข้อมูล', ' ใช้เพื่อเก็บข้อมูลส ารอง', 'เข้ารหัสเพื่อส่งข้อมูล', 'แสดงชื่อผู้ใช้ในระบบ', 'c', '', '', '', '', ''),
(25, 43, 1, '9. ข้อใดเป็นความสามารถของ Anti-malware?', ' ป้องกนัไวรัสเท่าน้ัน', ' ป้องกันมัลแวร์ทุกรูปแบบ', 'ป้องกันเฉพาะโฆษณา', 'ใช้ส าหรับจัดการบัญชีผู้ใช', 'b', '', '', '', '', ''),
(26, 42, 1, '3.คำว่า Vulnerability หมายถึงอะไรในระบบความมนั่ คงสารสนเทศ?', 'ช่องทางการสื่อสาร', 'ช่องโหว่หรือจุดอ่อนของระบบ', 'วิธีเข้ารหัสข้อมูล', 'วิธีเข้าถึงระบบอย่างถูกต้อง', 'b', '', '', '', '', ''),
(27, 42, 1, '4. ความเสี่ยง (Risk) เกิดจากอะไร?', 'การใช้ซอฟต์แวร์ของแท', 'ความเป็นไปได้ของภัยคุกคามที่ใช้ช่องโหว่', 'การอัปเดตระบบสม ่าเสมอ', 'ระบบที่มีประสิทธิภาพ', 'b', '', '', '', '', ''),
(28, 42, 1, '10. ข้อใดคือประโยชน์ของ VPN? ', ' เพิ่มความเร็วเน็ต', ' สร้างไฟล์สำรอง', 'ปกป้องข้อมูลระหว่างส่งผ่านเครือข่าย', ' ลดค่าใช้จ่ายระบบ', 'c', '', '', '', '', ''),
(29, 44, 1, 'ข้อใดคือขั ้นตอนแรกในวงจรการพัฒนาระบบความมั ่นคงของสารสนเทศ?', 'การนำไปใช้งาน (Implementation) ', 'การระบุความต้องการด้านความมั ่นคง (Security Requirements) ', 'การทดสอบระบบ (Testing) ', 'การบ ารุงรักษาระบบ (Maintenance)', 'b', '', '', '', '', ''),
(30, 44, 1, 'ในขั ้นตอนการวิเคราะห์ความเสี่ยง (Risk Assessment) สิ่งใดที่ต้องพิจารณา? ', 'ความเร็วของระบบ', 'ค่าใช้จ่ายในการพัฒนา ', 'ช่องโหว่และภัยคุกคาม', 'ความสวยงามของหน้าจอ', 'c', '', '', '', '', ''),
(31, 44, 1, 'การออกแบบระบบความมั ่นคงควรมีเป้าหมายใดเป็นหลัก?', 'ลดจำนวนผู ้ใช้งาน ', 'เพิ่มความซับซ้อน ', ' สร้างระบบที่ป้องกันภัยคุกคามได้อย่างเหมาะสม', 'ใช้ซอฟต์แวร์ที่มีราคาสูง ', 'c', '', '', '', '', ''),
(32, 44, 1, 'การน าระบบความมั ่นคงไปใช้งานจริง ควรคำนึงถึงเรื่องใด?', 'ความสวยงามของระบบ ', ' ความสะดวกของผู ้ใช้งานและความปลอดภัย ', 'การใช้กราฟิกคุณภาพสูง ', 'ความสามารถในการสร้างรายงานทางบัญชี ', 'b', '', '', '', '', ''),
(33, 44, 1, ' การทดสอบระบบความมั ่นคงมักใช้วิธีใด? ', 'การเทียบสีในระบบ ', 'การสำรวจผู ้ใช้งาน ', 'การทดสอบการเจาะระบบ (Penetration Testing) ', 'การใช้สคริปต์ตกแต่งหน้าจอ ', 'c', '', '', '', '', ''),
(34, 45, 1, 'วงจรการพัฒนาระบบความมั ่นคงมีลักษณะอย่างไร? ', 'แบบเส้นตรง ', 'แบบไม่แน่นอน ', 'แบบวงกลมต่อเนื ่อง ', 'แบบกลุ ่มซ้อนกัน ', 'c', '', '', '', '', ''),
(35, 45, 1, 'การฝึกอบรมผู ้ใช้งานในระบบใหม่ มีจุดประสงค์ใด? ', 'ลดค่าใช้จ่าย ', 'ให้ผู ้ใช้รู ้วิธีใช้ระบบอย่างปลอดภัย ', 'เพิ่มการขาย', 'ลดการใช้ไฟฟ้า ', 'b', '', '', '', '', ''),
(36, 45, 1, ' การปรับปรุงและบ ารุงรักษาระบบมีวัตถุประสงค์ใด? ', 'ปรับเปลี่ยนโลโก้ ', 'เพิ่มลูกเล่นใหม่ ', 'ป้องกันและแก้ไขช่องโหว่ที่เกิดขึ ้น', 'เพิ่มสีสันในระบบ ', 'c', '', '', '', '', ''),
(37, 45, 1, 'การจัดท าเอกสารระบบความมั ่นคงมีประโยชน์ใด? ', 'เพื่อการโฆษณา ', ' เพื่อการจัดซื ้ออุปกรณ', 'เพื่อให้ทีมงานสามารถตรวจสอบและบ ารุงรักษาได้ ', 'เพื่อท ารายงานการเงิน ', 'c', '', '', '', '', ''),
(38, 45, 1, 'การระบุความต้องการด้านความมั ่นคงควรรวมสิ่งใดบ้าง? ', 'งบประมาณของโครงการ ', 'ความต้องการของผู ้ใช้งานและข้อก าหนดด้านความปลอดภัย ', 'ลักษณะหน้าจอโปรแกรม ', 'รายชื ่อผู ้พัฒนา ', 'b', '', '', '', '', ''),
(39, 46, 1, 'ข้อใดกล่าวถึงวัตถุประสงค์หลักของการเข้ารหัสข้อมูล (Encryption) ได้ถูกต้องที่สุด?', ' ทำให้ไฟล์มีขนาดเล็กลง', 'ป้องกันไวรัสเข้าสู ่ระบบ ', ' รักษาความลับของข้อมูลขณะส่งผ่านเครือข่าย ', 'ลดความซับซ้อนของข้อมูล ', 'c', '', '', '', '', ''),
(40, 46, 1, ' การเข้ารหัสแบบ Symmetric Encryption มีลักษณะเด่นคืออะไร?', 'ใช้คีย์ 2 ชุด ', ' ใช้รหัสผ่านที่แตกต่างในการเข้ารหัสและถอดรหัส', 'ใช้คีย์เดียวกันในการเข้ารหัสและถอดรหัส ', 'ไม่สามารถถอดรหัสได้ ', 'c', '', '', '', '', ''),
(41, 46, 1, 'อัลกอริธึมการเข้ารหัสแบบไม่สมมาตร (Asymmetric Encryption) ใช้คีย์กี ่ชุด? ', '1 ชุด', '2 ชุด คือ Public Key และ Private Key', '3 ชุด ', 'ไม่มีการใช้คีย์ ', 'b', '', '', '', '', ''),
(42, 46, 1, ' ข้อใดคือตัวอย่างของการใช้งาน Public Key ในชีวิตจริง?', 'การตั้งรหัสผ่าน Wi-Fi ', 'การสแกนลายนิ้วมือ ', 'การยืนยันตัวตนผ่าน HTTPS บนเว็บไซต์ ', 'การใช้ Antivirus ', 'c', '', '', '', '', ''),
(43, 46, 1, 'ข้อใดคือลักษณะของ Hash Function? ', ' ทำให้ข้อความกลับมาเหมือนเดิมได้ ', 'ใช้สำหรับเข้ารหัสลับ ', 'แปลงข้อมูลเป็นค่าคงที่ที่ไม่สามารถย้อนกลับได้', 'ใช้ถอดรหัสข้อความ ', 'c', '', '', '', '', ''),
(44, 47, 1, 'อัลกอริธึมใดต่อไปนี ้เป็นการเข้ารหัสแบบสมมาตร? ', 'RSA', 'DES ', 'ECC ', 'DSA ', 'b', '', '', '', '', ''),
(45, 47, 1, 'ข้อใดแสดงต าแหน่งของ Firewall บนโครงสร้างเครือข่ายได้ถูกต้อง? ', 'วางหลัง Router ', ' วางหน้าผู ้ใช้งาน', 'วางระหว่างเครือข่ายภายในและภายนอก', 'วางในเครื่องผู ้ใช้ ', 'c', 'Capture.JPG', '', '', '', ''),
(46, 47, 1, 'SSL/TLS ท าหน้าที ่ใดในกระบวนการสื ่อสารออนไลน์? ', ' ลดเวลาโหลดเว็บไซต์ ', ' ป้องกันการเข้าถึงข้อมูลจากบุคคลที่สาม', 'ทำให้เว็บสวยงามขึ ้น ', 'บีบอัดข้อมูลเว็บไซต์ ', 'b', '', '', '', '', ''),
(47, 47, 1, 'ข้อใดเป็นความแตกต่างระหว่าง Symmetric และ Asymmetric Encryption?', 'Symmetric ใช้ 2 คีย์ ส่วน Asymmetric ใช้คีย์เดียว ', ' Asymmetric ใช้ Public/Private Key คู ่กัน ส่วน Symmetric ใช้คีย์เดียว ', 'ไม่มีความแตกต่าง', ' Symmetric ไม่ใช้คีย์ใดๆ ', 'b', '', '', '', '', ''),
(48, 47, 1, ' การเข้ารหัสที ่มีความเร็วสูงและเหมาะส าหรับปริมาณข้อมูลมากคือแบบใด? ', 'Asymmetric', ' Symmetric ', 'Hashing ', ' Two-Factor ', 'b', '', '', '', '', ''),
(49, 48, 1, 'ข้อใดเป็นวัตถุประสงค์หลักของกฎหมายคอมพิวเตอร์?', 'ส่งเสริมการละเมิดลิขสิทธิ ์ ', 'ปกป้องข้อมูลและความเป็นส่วนตัวของผู ้ใช้', ' สนับสนุนการโจมตีทางไซเบอร์ ', 'ท าลายข้อมูลในระบบ', 'b', '', '', '', '', ''),
(50, 48, 1, 'ข้อใดถือเป็นการกระทำผิดตามกฎหมายคอมพิวเตอร์?', 'การเผยแพร่ไวรัสคอมพิวเตอร์ ', 'การส่งอีเมลทักทายเพื่อน', 'การใช้ซอฟต์แวร์ลิขสิทธิ ์อย่างถูกต้อง ', 'การสำรองข้อมูลส่วนตัว ', 'a', '', '', '', '', ''),
(51, 48, 1, 'หลักจริยธรรมที ่สำคัญในการใช้เทคโนโลยีสารสนเทศคือข้อใด?', 'การลอกข้อมูลจากผู ้อื่น ', 'การใช้ข้อมูลอย่างรับผิดชอบและเคารพสิทธิผู ้อื่น ', 'การแฮกข้อมูลเพื่อความสนุกสนาน', 'การเผยแพร่ข้อมูลเท็จ', 'b', '', '', '', '', ''),
(52, 48, 1, ' ข้อใดคือหลักการ “ความเป็นส่วนตัว” ในระบบสารสนเทศ? ', 'เปิดเผยข้อมูลของผู ้อื่นโดยไม่ได้รับอนุญาต ', 'ปกป้องข้อมูลส่วนบุคคลไม่ให้ถูกเข้าถึงโดยไม่ได้รับอนุญาต ', ' การเข้าถึงข้อมูลทั ้งหมดในระบบได้โดยเสรี ', ' การละเมิดข้อมูลส่วนตัว ', 'b', '', '', '', '', ''),
(53, 48, 1, 'พ.ร.บ. คอมพิวเตอร์ พ.ศ. 2560 ในประเทศไทยเน้นเรื ่องใดเป็นส าคัญ?', 'การสนับสนุนการโจมตีไซเบอร์ ', 'การควบคุมและป้องกันการกระท าผิดทางคอมพิวเตอร์', 'การส่งเสริมการลอกเลียนแบบข้อมูล ', 'การสนับสนุนการละเมิดลิขสิทธิ ์', 'b', '', '', '', '', ''),
(54, 49, 1, 'ข้อใดเป็นความรับผิดชอบของผู้ใช้งานระบบสารสนเทศตามจริยธรรม?', 'ละเมิดข้อมูลของผู ้อื่นเพื่อผลประโยชน์ส่วนตัว ', ' ใช้เทคโนโลยีเพื่อช่วยพัฒนาสังคมและปฏิบัติตามกฎหมาย', 'เปิดเผยรหัสผ่านของผู ้อื่นโดยไม่อนุญาต ', 'ใช้ซอฟต์แวร์เถื ่อนอย่างเปิดเผย', 'b', '', '', '', '', ''),
(55, 49, 1, 'ข้อใดไม่ถือเป็นการละเมิดสิทธิ ์ตามกฎหมายคอมพิวเตอร์?', 'การเจาะระบบฐานข้อมูลของบริษัท ', 'การใช้งานซอฟต์แวร์ลิขสิทธิ ์อย่างถูกต้อง', 'การส่งอีเมลขยะ (Spam) ', 'การปลอมแปลงข้อมูลออนไลน์ ', 'b', '', '', '', '', ''),
(56, 49, 1, ' ข้อใดคือแนวทางปฏิบัติที ่ถูกต้องในการรักษาความมั ่นคงของข้อมูลส่วนบุคคล?', 'แชร์รหัสผ่านกับเพื่อน ', ' ไม่เปิดเผยข้อมูลส่วนตัวในที่สาธารณะโดยไม่จ าเป็น ', ' ส่งข้อมูลส่วนตัวผ่านอีเมลที่ไม่ปลอดภัย', 'ใช้รหัสผ่านง่าย ๆ เช่น \"123456\" ', 'b', '', '', '', '', ''),
(57, 49, 1, ' การใช้เทคโนโลยีสารสนเทศโดยค านึงถึงผลกระทบทางสังคมและสิ ่งแวดล้อมเป็นหลักการของข้อใด? ', 'ความรับผิดชอบทางจริยธรรม ', 'การละเมิดลิขสิทธิ ์', 'การแฮกข้อมูล', 'การละเมิดความเป็นส่วนตัว ', 'a', '', '', '', '', ''),
(58, 49, 1, 'ข้อใดคือผลที ่อาจเกิดขึ ้นจากการละเมิดกฎหมายคอมพิวเตอร์? ', ' การได้รับรางวัล ', 'การถูกด าเนินคดีทางกฎหมายและโทษทางอาญา ', 'การได้รับการยกย่อง ', 'ไม่มีผลกระทบใด ๆ ', 'b', '', '', '', '', ''),
(59, 50, 1, 'Intrusion Detection System (IDS) คืออะไร? ', 'ระบบที่ป้องกันไวรัส ', 'ระบบที่ตรวจจับและแจ้งเตือนการบุกรุกในระบบเครือข่าย ', 'ระบบสำรองข้อมูลอัตโนมัติ ', 'ระบบจัดเก็บข้อมูล ', 'b', '', '', '', '', ''),
(60, 50, 1, 'IDS แบบใดที ่ตรวจจับการบุกรุกโดยเปรียบเทียบพฤติกรรมกับลายเซ็นที ่รู ้จัก?', 'Anomaly-based IDS', 'Signature-based IDS', 'Hybrid IDS', 'Firewall ', 'b', '', '', '', '', ''),
(61, 50, 1, 'ข้อใดคือข้อดีของ Signature-based IDS?', 'สามารถตรวจจับภัยใหม่ที่ไม่เคยรู ้จักได้ดี ', 'มีความแม่นย าสูงส าหรับภัยที่รู ้จัก', 'ไม่ต้องการอัปเดตฐานข้อมูลลายเซ็น ', 'ใช้งานง่ายโดยไม่ต้องตั้งค่า ', 'b', '', '', '', '', ''),
(62, 50, 1, 'IDS แบบใดที ่ตรวจจับการบุกรุกโดยการวิเคราะห์พฤติกรรมที ่ผิดปกติจากปกติ? ', 'Signature-based IDS ', 'Anomaly-based IDS ', 'Firewall ', 'Proxy Server ', 'b', '', '', '', '', ''),
(63, 50, 1, 'ข้อใดเป็นข้อจำกัดของ Anomaly-based IDS?', 'ไม่สามารถตรวจจับภัยที่รู ้จักได้ ', 'มีโอกาสแจ้งเตือนผิดพลาดสูง (False Positive) ', 'ไม่ต้องการอัปเดตฐานข้อมูล', 'ตรวจจับได้เร็วกว่า Signature-based IDS เสมอ', 'b', '', '', '', '', ''),
(64, 51, 1, 'ข้อใดไม่ใช่ส่วนประกอบหลักของ IDS? ', 'Sensor (ตัวเก็บข้อมูล) ', 'Analyzer (ตัววิเคราะห์ข้อมูล) ', 'Reporter (ตัวรายงานผล)', 'Firewall (กำแพงป้องกัน) ', 'd', '', '', '', '', ''),
(65, 51, 1, 'ระบบ IDS ใดที ่ติดตั ้งบนเครื ่องเซิร์ฟเวอร์เพื ่อป้องกันเครื ่องนั ้นโดยเฉพาะ? ', 'Network-based IDS (NIDS) ', 'Host-based IDS (HIDS) ', 'Firewall ', 'Proxy Server ', 'b', '', '', '', '', ''),
(66, 51, 1, 'ข้อใดคือความแตกต่างหลักระหว่าง Network-based IDS และ Host-based IDS?', 'NIDS ตรวจสอบข้อมูลในเครือข่ายโดยรวม ส่วน HIDS ตรวจสอบในเครื่องเดียว ', 'NIDS ใช้ตรวจจับไวรัส ส่วน HIDS ใช้ตรวจจับสแปม', 'NIDS ใช้ส าหรับการส ารองข้อมูล ส่วน HIDS ใช้ส าหรับการเข้ารหัส ', 'ไม่มีความแตกต่าง ', 'a', '', '', '', '', ''),
(67, 51, 1, 'การแจ้งเตือนที ่ผิดพลาด (False Positive) หมายถึงอะไร?', 'การแจ้งเตือนเมื่อไม่มีการบุกรุกเกิดขึ ้นจริง ', 'การไม่แจ้งเตือนเมื่อมีการบุกรุกจริง ', 'การแจ้งเตือนถูกต้องทุกครั ้ง ', 'การปิดระบบโดยอัตโนมัติ', 'a', '', '', '', '', ''),
(68, 51, 1, 'ข้อใดเป็นตัวอย่างของการตอบสนองหลังจาก IDS ตรวจจับการบุกรุก?', 'การแจ้งเตือนผู ้ดูแลระบบ ', ' การเพิ่มความเร็วอินเทอร์เน็ต', 'การลบข้อมูลทั ้งหมด ', ' การปิดระบบเครือข่ายถาวร', 'a', '', '', '', '', '');

-- --------------------------------------------------------

--
-- Table structure for table `quiz`
--

CREATE TABLE `quiz` (
  `quiz_id` int(11) NOT NULL,
  `quiz_name` varchar(100) NOT NULL,
  `lesson_id` int(11) NOT NULL,
  `passing_percentage` int(11) NOT NULL,
  `quiz_date` datetime NOT NULL,
  `quiz_type` enum('Pre-test','Post_test','','') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `quiz`
--

INSERT INTO `quiz` (`quiz_id`, `quiz_name`, `lesson_id`, `passing_percentage`, `quiz_date`, `quiz_type`) VALUES
(42, 'Pre-test', 6, 0, '2025-06-19 02:44:01', 'Pre-test'),
(43, 'Post-test', 6, 80, '2025-07-17 13:30:41', 'Post_test'),
(44, 'Pre-test', 7, 0, '2025-07-21 10:26:55', 'Pre-test'),
(45, 'Post-test', 7, 80, '2025-07-21 10:32:27', 'Post_test'),
(46, 'Pre-test', 8, 0, '2025-07-24 13:36:06', 'Pre-test'),
(47, 'Post-test', 8, 80, '2025-07-24 13:39:54', 'Post_test'),
(48, 'Pre-test', 9, 0, '2025-07-31 01:22:42', 'Pre-test'),
(49, 'Post-test', 9, 80, '2025-07-31 01:28:59', 'Post_test'),
(50, 'Pre-test', 11, 0, '2025-07-31 13:24:51', 'Pre-test'),
(51, 'Post-test', 11, 80, '2025-07-31 13:28:51', 'Post_test');

-- --------------------------------------------------------

--
-- Table structure for table `quiz_video`
--

CREATE TABLE `quiz_video` (
  `video_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `youtube_link` varchar(255) NOT NULL,
  `description` text,
  `time_duration` varchar(50) DEFAULT NULL,
  `preview` text,
  `video_image` varchar(255) DEFAULT NULL,
  `quiz_id` int(11) DEFAULT NULL,
  `lesson_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `quiz_video`
--

INSERT INTO `quiz_video` (`video_id`, `title`, `youtube_link`, `description`, `time_duration`, `preview`, `video_image`, `quiz_id`, `lesson_id`) VALUES
(62, 'Pre-test', '', NULL, NULL, NULL, NULL, 42, 6),
(63, 'บทที่1 แบบทดสอบพื้นฐานความมั่นคงของระบบสารสนเทศ', 'https://youtu.be/Coh7oRmw9cs?si=dupdGug80EGq3r29', 'Information System Security | หน่วยที่ 1 ความรู้พื้นฐานเกี่ยวกับความมั่นคงของระบบสารสนเทศ\r\n', '11:21', NULL, '', NULL, 6),
(64, 'Post-test', '', NULL, NULL, NULL, NULL, 43, 6),
(65, 'Pre-test', '', NULL, NULL, NULL, NULL, 44, 7),
(66, 'บทที่2 วงจรการพัฒนาระบบความมั ่นคงของระบบสารสนเทศ', 'https://youtu.be/6FGpjd485c4?si=ZKkXuvI_Ty3yB9cg', '', '17:41', NULL, '', NULL, 7),
(67, 'Post-test', '', NULL, NULL, NULL, NULL, 45, 7),
(68, 'Pre-test', '', NULL, NULL, NULL, NULL, 46, 8),
(69, 'หน่วยที่3 วิธีการและเทคนิครักษาความมั ่นคงของระบบ  สารสนเทศ', 'https://youtu.be/Nh5npqoTLLQ?si=8S8oIQI3ALCxclJY', '', '17:20', NULL, '', NULL, 8),
(70, 'Post-test', '', NULL, NULL, NULL, NULL, 47, 8),
(71, 'Pre-test', '', NULL, NULL, NULL, NULL, 48, 9),
(72, 'หน่วยที่4 นโยบายในการสร้างความมั ่นคงของระบบสารสนเทศ', 'https://youtu.be/RceFsg0h_Zw?si=QzJ1oLMaQhXSV7P3', '', '8:01', NULL, '', NULL, 9),
(73, 'Post-test', '', NULL, NULL, NULL, NULL, 49, 9),
(74, 'Pre-test', '', NULL, NULL, NULL, NULL, 50, 11),
(75, 'หน่วยที่5 กลไกในการสร้างความปลอดภัยและเครื ่องมือช่วยใน  การสร้างมั่นคงของระบบสารสนเทศ', 'https://youtu.be/oPPN7Q6DEvg?si=i2iFDNzCgRrWWhCf', '', '5:01', NULL, '', NULL, 11),
(76, 'Post-test', '', NULL, NULL, NULL, NULL, 51, 11);

-- --------------------------------------------------------

--
-- Table structure for table `registered_courses`
--

CREATE TABLE `registered_courses` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `registered_courses`
--

INSERT INTO `registered_courses` (`id`, `user_id`, `course_id`, `registered_at`) VALUES
(33, 34, 12, '2025-08-21 00:12:26'),
(34, 1, 12, '2025-08-21 00:25:31');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `username` varchar(100) NOT NULL,
  `id_card` varchar(13) NOT NULL,
  `gender` enum('male','female','other') NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('user') NOT NULL DEFAULT 'user',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `profile_image` varchar(255) NOT NULL DEFAULT 'default.jpg',
  `tel` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `first_name`, `last_name`, `email`, `username`, `id_card`, `gender`, `password`, `role`, `created_at`, `profile_image`, `tel`) VALUES
(1, 'ice', 'supichet', 'dddff@gmail.com', 'user1', '4256789876534', '', 'scrypt:32768:8:1$FjkiC19YZvGRrNDQ$4ec07437a3f4df40a42223d855a31f18202e2c5fd0666a1fac69f596297afdc6f45df05a4f4888b910a1178311f11aa718fbda12b12fe7c3bd9ddb343b2ace03', 'user', '2025-08-20 17:25:16', '0_20250821002749_images.png', ''),
(34, 'pond', 'athittanat', 'qwer@gmail.com', 'user', '7777777754545', '', 'scrypt:32768:8:1$NUevnNNTHXSBUFvB$74d34d9e28b8030da208d104ba294a9c8e4c538b0385f874dcb2408e5eb49ce944735c159b00df4bd2a902b0289bb571a2fbbc37c6b57f82bf6029a6435bd253', 'user', '2025-06-09 09:41:39', '34_20250731135048_gg.png', '0987676789'),
(35, 'tee', 'komgrit', 'ddppgg@gmail.com', 'user2', '7777567754545', 'male', 'scrypt:32768:8:1$3ytS0lPxsQyRWB4I$0c0f6cd65158fb18e9c11c65d42ba1fc7e63deb2e97011ada9e79ad769c7f99903c4df911027729d6bc65a7573946a9cf1b43febfc649665fdcaebd53bc6f4f2', 'user', '2025-08-20 17:51:17', 'default.jpg', '');

-- --------------------------------------------------------

--
-- Table structure for table `user_lesson_progress`
--

CREATE TABLE `user_lesson_progress` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `video_id` int(11) NOT NULL,
  `lesson_id` int(11) NOT NULL,
  `is_completed` tinyint(1) DEFAULT '0',
  `completed_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `user_quiz_attempts`
--

CREATE TABLE `user_quiz_attempts` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `score` int(11) DEFAULT '0',
  `total_questions` int(11) NOT NULL,
  `percentage` decimal(5,2) NOT NULL,
  `passed` tinyint(1) DEFAULT '0',
  `attempt_date` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `user_quiz_attempts`
--

INSERT INTO `user_quiz_attempts` (`id`, `user_id`, `quiz_id`, `score`, `total_questions`, `percentage`, `passed`, `attempt_date`) VALUES
(14, 34, 42, 2, 5, '40.00', 1, '2025-08-21 00:12:44'),
(15, 34, 43, 4, 5, '80.00', 1, '2025-08-21 00:14:26'),
(16, 34, 44, 0, 5, '0.00', 1, '2025-08-21 00:15:05'),
(17, 34, 45, 3, 5, '60.00', 0, '2025-08-21 00:15:21'),
(18, 34, 45, 3, 5, '60.00', 0, '2025-08-21 00:18:23'),
(19, 34, 45, 3, 5, '60.00', 0, '2025-08-21 00:18:51'),
(20, 34, 45, 4, 5, '80.00', 1, '2025-08-21 00:19:36'),
(21, 34, 46, 1, 5, '20.00', 1, '2025-08-21 00:19:45'),
(22, 34, 47, 4, 5, '80.00', 1, '2025-08-21 00:20:00'),
(23, 34, 48, 0, 5, '0.00', 1, '2025-08-21 00:20:31'),
(24, 34, 49, 4, 5, '80.00', 1, '2025-08-21 00:20:53'),
(25, 34, 50, 1, 5, '20.00', 1, '2025-08-21 00:21:02'),
(26, 34, 51, 2, 5, '40.00', 0, '2025-08-21 00:21:23'),
(27, 34, 51, 4, 5, '80.00', 1, '2025-08-21 00:23:13'),
(28, 1, 42, 1, 5, '20.00', 1, '2025-08-21 00:25:42'),
(29, 1, 43, 1, 5, '20.00', 0, '2025-08-21 00:25:57'),
(30, 1, 43, 3, 5, '60.00', 0, '2025-08-21 00:26:06'),
(31, 1, 43, 4, 5, '80.00', 1, '2025-08-21 00:26:14'),
(32, 1, 44, 2, 5, '40.00', 1, '2025-08-21 00:26:25');

-- --------------------------------------------------------

--
-- Table structure for table `user_video_progress`
--

CREATE TABLE `user_video_progress` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `video_id` int(11) NOT NULL,
  `completed_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `user_video_progress`
--

INSERT INTO `user_video_progress` (`id`, `user_id`, `video_id`, `completed_at`) VALUES
(9, 34, 63, '0000-00-00 00:00:00'),
(10, 34, 66, '0000-00-00 00:00:00'),
(11, 34, 69, '0000-00-00 00:00:00'),
(12, 34, 72, '0000-00-00 00:00:00'),
(13, 34, 75, '0000-00-00 00:00:00'),
(14, 0, 63, '0000-00-00 00:00:00'),
(15, 0, 66, '0000-00-00 00:00:00');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `instructor_id` (`instructor_id`),
  ADD KEY `categories_id` (`categories_id`);

--
-- Indexes for table `course_completions`
--
ALTER TABLE `course_completions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_course_unique` (`user_id`,`course_id`),
  ADD KEY `fk_completions_courses_relation` (`course_id`);

--
-- Indexes for table `instructor`
--
ALTER TABLE `instructor`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `lesson`
--
ALTER TABLE `lesson`
  ADD PRIMARY KEY (`lesson_id`),
  ADD KEY `fk_lesson_to_courses_link` (`course_id`);

--
-- Indexes for table `questions`
--
ALTER TABLE `questions`
  ADD PRIMARY KEY (`question_id`),
  ADD KEY `fk_quiz` (`quiz_id`);

--
-- Indexes for table `quiz`
--
ALTER TABLE `quiz`
  ADD PRIMARY KEY (`quiz_id`),
  ADD KEY `fk_quiz_lesson` (`lesson_id`);

--
-- Indexes for table `quiz_video`
--
ALTER TABLE `quiz_video`
  ADD PRIMARY KEY (`video_id`),
  ADD KEY `fk_quiz_video_quiz` (`quiz_id`),
  ADD KEY `fk_quiz_video_lesson` (`lesson_id`);

--
-- Indexes for table `registered_courses`
--
ALTER TABLE `registered_courses`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`course_id`),
  ADD KEY `course_id` (`course_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user_lesson_progress`
--
ALTER TABLE `user_lesson_progress`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`video_id`),
  ADD KEY `video_id` (`video_id`),
  ADD KEY `lesson_id` (`lesson_id`);

--
-- Indexes for table `user_quiz_attempts`
--
ALTER TABLE `user_quiz_attempts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `quiz_id` (`quiz_id`);

--
-- Indexes for table `user_video_progress`
--
ALTER TABLE `user_video_progress`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `video_id` (`video_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `course_completions`
--
ALTER TABLE `course_completions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `instructor`
--
ALTER TABLE `instructor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `lesson`
--
ALTER TABLE `lesson`
  MODIFY `lesson_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `questions`
--
ALTER TABLE `questions`
  MODIFY `question_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=69;

--
-- AUTO_INCREMENT for table `quiz`
--
ALTER TABLE `quiz`
  MODIFY `quiz_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=52;

--
-- AUTO_INCREMENT for table `quiz_video`
--
ALTER TABLE `quiz_video`
  MODIFY `video_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=77;

--
-- AUTO_INCREMENT for table `registered_courses`
--
ALTER TABLE `registered_courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT for table `user_quiz_attempts`
--
ALTER TABLE `user_quiz_attempts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT for table `user_video_progress`
--
ALTER TABLE `user_video_progress`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `fk_courses_categories_relation` FOREIGN KEY (`categories_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_courses_instructor_relation` FOREIGN KEY (`instructor_id`) REFERENCES `instructor` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Constraints for table `course_completions`
--
ALTER TABLE `course_completions`
  ADD CONSTRAINT `fk_completions_courses_relation` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_completions_user_relation` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `lesson`
--
ALTER TABLE `lesson`
  ADD CONSTRAINT `fk_lesson_courses_relation` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `questions`
--
ALTER TABLE `questions`
  ADD CONSTRAINT `fk_questions_quiz_relation` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`quiz_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `quiz`
--
ALTER TABLE `quiz`
  ADD CONSTRAINT `fk_quiz_lesson_relation` FOREIGN KEY (`lesson_id`) REFERENCES `lesson` (`lesson_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `quiz_video`
--
ALTER TABLE `quiz_video`
  ADD CONSTRAINT `fk_quizvideo_lesson_relation` FOREIGN KEY (`lesson_id`) REFERENCES `lesson` (`lesson_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `registered_courses`
--
ALTER TABLE `registered_courses`
  ADD CONSTRAINT `fk_regcourses_courses_relation` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_regcourses_user_relation` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `user_quiz_attempts`
--
ALTER TABLE `user_quiz_attempts`
  ADD CONSTRAINT `fk_attempts_quiz_relation` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`quiz_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `user_video_progress`
--
ALTER TABLE `user_video_progress`
  ADD CONSTRAINT `fk_progress_video_relation` FOREIGN KEY (`video_id`) REFERENCES `quiz_video` (`video_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
