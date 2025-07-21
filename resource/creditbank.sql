-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 21, 2025 at 10:00 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`id`, `first_name`, `last_name`, `email`, `username`, `gender`, `password`, `role`, `tel`, `profile_image`) VALUES
(3, 'admin', 'teste', 'admin@gmail.com', 'admin', 'Male', 'scrypt:32768:8:1$vkJUSWAzx0Vsmj98$0ca7495f5c23fb3065e2258f3087160b9dfb8167b0596a3ba664f7dd4f87953e799eada96e4022b91232aac0cba897fa05c4644da9f826d63a3879cce47f0d8d', 'admin', '0987676774', '1.jpg'),
(7, 'supap', 'rukdee', 'asdadasd@gmail.com', 'tests1234', 'Male', 'scrypt:32768:8:1$twRmfoNf9zTyjogk$30ba73f74e0b685b6ba47cc895c1b8c12b80a97b6ac6cb94b8e212600f39e9340c3e3b6055b9e3d2904995ac73a4c869bb3e4b94e20fdf6c833bd0dfef6c3b57', 'admin', '0944334455', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE `categories` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `instructor_id` int(11) NOT NULL,
  `categories_id` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `status` enum('publish','draft') NOT NULL DEFAULT 'draft',
  `featured_video` varchar(300) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`id`, `featured_image`, `title`, `created_at`, `instructor_id`, `categories_id`, `description`, `status`, `featured_video`) VALUES
(12, 'testy.jpg', 'Information Systems Security', '2025-06-16 19:00:01', 6, 1, 'gwrgwregwrgwgwrgw', 'publish', NULL);

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `instructor`
--

INSERT INTO `instructor` (`id`, `first_name`, `last_name`, `email`, `username`, `gender`, `password`, `role`, `tel`, `profile_image`) VALUES
(6, 'jamjann', 'mungpijit', 'instructor@gmail.com', 'instructor', 'Female', 'scrypt:32768:8:1$zBTKTEERcHaUHLtz$138f13bcafffe559ac5c294ffa493f010e93b3294351e8b48ee76910a2f58afc555df4ae45e2dc50ae9ee7b69e5fecb8cb79c3b590d4708e65ad93572a9d7ffc', 'instructor', '0944334433', 'jpg'),
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
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lesson`
--

INSERT INTO `lesson` (`lesson_id`, `lesson_name`, `lesson_date`, `course_id`, `instructor_id`, `description`) VALUES
(6, 'บทที่1 แบบทดสอบพนฐานความมนคงของระบบสารสนเทศ', '2025-06-16 19:02:27', 12, 6, NULL),
(7, 'บทที่ 2 วงจรการพัฒนาระบบความมั ่นคงของระบบสารสนเทศ', '2025-07-20 00:00:00', 12, 6, NULL);

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `questions`
--

INSERT INTO `questions` (`question_id`, `quiz_id`, `score`, `question_name`, `choice_a`, `choice_b`, `choice_c`, `choice_d`, `correct_answer`, `question_image`, `choice_a_image`, `choice_b_image`, `choice_c_image`, `choice_d_image`) VALUES
(19, 42, 1, '1. ข้อใดคือองค์ประกอบของความมั ่นคงสารสนเทศ (CIA Triad)?', 'Control, Integrity, Accuracy ', 'Confidentiality, Integrity, Availability', 'Communication, Innovation, Access ', ' Compliance, Information, Audit ', 'b', '', '', '', '', ''),
(20, 42, 1, '2. ข้อใดอธิบายคำว่า Threat ได้ถูกต้องที่สุด? ', ' ช่องโหว่ในระบบ', 'วิธีการที่ใช้ป้องกันข้อมูล', ' ความเสี่ยงทางการเงิน', 'สงทที่อาจก่อให้เกิดอันตรายต่อระบบ ', 'd', '', '', '', '', ''),
(21, 42, 1, '3. คำว่า Vulnerability หมายถึงอะไรในระบบความมั่นคงสารสนเทศ? ', 'ช่องทางการสื่อสาร ', 'ช่องโหว่หรือจุดอ่อนของระบบ ', 'วิธีเข้ารหัสข้อมูล ', 'วิธีเข้าถึงระบบอย่างถูกต้อง ', 'b', '', '', '', '', ''),
(22, 42, 1, '4. ความเสี่ยง (Risk) เกิดจากอะไร? ', 'การใช้ซอฟต์แวร์ของแท้ ', 'ความเป็นไปได้ของภัยคุกคามที่ใช้ช่องโหว่ ', 'การอัปเดตระบบสม ่าเสมอ ', 'ระบบที่มีประสิทธิภาพ', 'b', '', '', '', '', ''),
(23, 42, 1, '5. ข้อใดไม่ใช่ประเภทของ Security Control?', 'Physical Control', 'Administrative Control', 'Technical Control ', 'Financial Control ', 'd', '', '', '', '', ''),
(24, 43, 1, '5. ข้อใดไม่ใช่ประเภทของ Security Control? ', 'Physical Control', 'Administrative Control', 'Technical Control ', ' Financial Control ', 'd', '', '', '', '', ''),
(25, 43, 1, '6. Firewall ทำหน้าที่อะไร?', ' ตรวจสอบความเร็วอินเทอร์เน็ต ', 'ป้องกันการเข้าถึงเครือข่ายโดยไม่ได้รับอนุญาต ', ' เข้ารหัสขอมูลทั้งหมด ', ' บันทึกการใช้งานเว็บไซต์ ', 'b', '', '', '', '', ''),
(26, 43, 1, '7. ข้อใดคือความแตกต่างหลักระหว่าง IDS และ IPS? ', 'IDS ป้องกันไวรัส, IPS ตรวจสอบอินเทอร์เน็ต', ' IDS ตรวจจับ, IPS ป้องกัน', ' IDS เก็บข้อมูล, IPS สร้างรหัสผ่าน ', 'IDS คือฮาร์ดแวร์, IPS คือซอฟต์แวร์ ', 'b', '', '', '', '', ''),
(27, 43, 1, ' Public Key ใช้ท าอะไร? ', 'ถอดรหัสข้อมูล ', ' ใช้เพื่อเก็บข้อมูลส ารอง ', ' เข้ารหัสเพื่อส่งข้อมูล ', ' แสดงชื่อผู ้ใช้ในระบบ', 'c', '', '', '', '', ''),
(28, 43, 1, 'ข้อใดเป็นความสามารถของ Anti-malware? ', 'ป้องกันไวรัสเท่านั้น ', ' ป้องกันมัลแวร์ทุกรูปแบบ ', ' ป้องกันเฉพาะโฆษณา', ' ใช้ส าหรับจัดการบัญชีผู ้ใช้ ', 'b', '', '', '', '', ''),
(29, 44, 1, '1. ข้อใดคือขั ้นตอนแรกในวงจรการพัฒนาระบบความมั ่นคงของสารสนเทศ?', 'การนำไปใช้งาน (Implementation) ', ' การระบุความต้องการด้านความมั ่นคง (Security Requirements) ', 'การทดสอบระบบ (Testing) ', 'การบ ารุงรักษาระบบ (Maintenance) ', 'b', '', '', '', '', ''),
(31, 44, 1, '2. ในขั้นตอนการวิเคราะห์ความเสี่ยง (Risk Assessment) สิ่งใดที่ต้องพิจารณา? ', 'ความเร็วของระบบ', 'ค่าใช้จ่ายในการพัฒนา ', 'ช่องโหว่และภัยคุกคาม ', 'ความสวยงามของหน้าจอ', 'c', '', '', '', '', ''),
(32, 44, 1, '3. การออกแบบระบบความมั่นคงควรมีเป้าหมายใดเป็นหลัก?', 'ลดจำนวนผู้ใช้งาน ', ' เพิ่มความซับซ้อน ', 'สร้างระบบที่ป้องกันภัยคุกคามได้อย่างเหมาะสม', ' ใช้ซอฟต์แวร์ที่มีราคาสูง', 'c', '', '', '', '', ''),
(33, 44, 1, '4. การน าระบบความมั ่นคงไปใช้งานจริง ควรคำนึงถึงเรื่องใด? ', ' ความสวยงามของระบบ', 'ความสะดวกของผู ้ใช้งานและความปลอดภัย ', ' การใช้กราฟิกคุณภาพสูง ', ' ความสามารถในการสร้างรายงานทางบัญช', 'b', '', '', '', '', ''),
(34, 44, 1, '5. การทดสอบระบบความมั่นคงมักใช้วิธีใด?', 'การเทียบสีในระบบ', 'การสำรวจผู้ใช้งาน', 'การทดสอบการเจาะระบบ (Penetration Testing)', ' การใช้สคริปต์ตกแต่งหน้าจอ', 'c', '', '', '', '', ''),
(35, 45, 1, '6. วงจรการพัฒนาระบบความมั ่นคงมีลักษณะอย่างไร? ', ' แบบเส้นตรง ', 'แบบไม่แน่นอน', 'แบบวงกลมต่อเนื่อง ', ' แบบกลุ่มซ้อนกัน ', 'c', '', '', '', '', ''),
(36, 45, 1, '7. การฝึกอบรมผู ้ใช้งานในระบบใหม่ มีจุดประสงค์ใด? ', 'ลดค่าใช้จ่าย ', ' ให้ผู ้ใช้รู ้วิธีใช้ระบบอย่างปลอดภัย', ' เพิ่มการขาย ', 'ลดการใช้ไฟฟ้า', 'b', '', '', '', '', ''),
(37, 45, 1, '8. การปรับปรุงและบ ารุงรักษาระบบมีวัตถุประสงค์ใด? ', 'ปรับเปลี่ยนโลโก', ' เพิ่มลูกเล่นใหม', 'ป้องกันและแก้ไขช่องโหว่ที่เกิดขึ ้น ', ' เพิ่มสีสันในระบบ', 'c', '', '', '', '', ''),
(38, 45, 1, '9. การจัดทำเอกสารระบบความมั ่นคงมีประโยชน์ใด? ', 'เพื่อการโฆษณา', 'เพื่อการจัดซื ้ออุปกรณ์ ', ' เพื่อให้ทีมงานสามารถตรวจสอบและบ ารุงรักษาได', ' เพื่อทำรายงานการเงิน ', 'c', '', '', '', '', ''),
(39, 45, 1, '10. การระบุความต้องการด้านความมั ่นคงควรรวมสิ่งใดบ้าง?', ' งบประมาณของโครงการ', ' ความต้องการของผู ้ใช้งานและข้อก าหนดด้านความปลอดภัย ', 'ลักษณะหน้าจอโปรแกรม', 'รายชื ่อผู ้พัฒนา', 'b', '', '', '', '', '');

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `quiz`
--

INSERT INTO `quiz` (`quiz_id`, `quiz_name`, `lesson_id`, `passing_percentage`, `quiz_date`, `quiz_type`) VALUES
(42, 'Pre-test', 6, 0, '2025-06-19 02:44:01', 'Pre-test'),
(43, 'Post-test', 6, 80, '2025-07-17 00:12:42', 'Post_test'),
(44, 'Pre-test', 7, 0, '2025-07-20 16:37:12', 'Pre-test'),
(45, 'Post-test', 7, 80, '2025-07-20 16:43:10', 'Post_test');

-- --------------------------------------------------------

--
-- Table structure for table `quiz_video`
--

CREATE TABLE `quiz_video` (
  `video_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `youtube_link` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `time_duration` varchar(50) DEFAULT NULL,
  `preview` text DEFAULT NULL,
  `video_image` varchar(255) DEFAULT NULL,
  `quiz_id` int(11) DEFAULT NULL,
  `lesson_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `quiz_video`
--

INSERT INTO `quiz_video` (`video_id`, `title`, `youtube_link`, `description`, `time_duration`, `preview`, `video_image`, `quiz_id`, `lesson_id`) VALUES
(62, 'Pre-test', '', NULL, NULL, NULL, NULL, 42, 6),
(63, 'บทที่1 แบบทดสอบพนฐานความมนคงของระบบสารสนเทศ', 'https://www.youtube.com/watch?v=LHH-8cd8ajU', '', '2.50', NULL, 'testy.jpg', NULL, 6),
(64, 'Post-test', '', NULL, NULL, NULL, NULL, 43, 6),
(65, 'Pre-test', '', NULL, NULL, NULL, NULL, 44, 7),
(66, 'บทที่ 2 วงจรการพัฒนาระบบความมั ่นคงของระบบสารสนเทศ', 'https://www.youtube.com/watch?v=rRg0BM6gnWU', '', '4', NULL, NULL, NULL, 7),
(67, 'Post-test', '', NULL, NULL, NULL, NULL, 45, 7);

-- --------------------------------------------------------

--
-- Table structure for table `registered_courses`
--

CREATE TABLE `registered_courses` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `registered_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `registered_courses`
--

INSERT INTO `registered_courses` (`id`, `user_id`, `course_id`, `registered_at`) VALUES
(33, 34, 12, '2025-07-21 01:38:03');

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
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `profile_image` varchar(255) NOT NULL DEFAULT 'default.jpg',
  `tel` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `first_name`, `last_name`, `email`, `username`, `id_card`, `gender`, `password`, `role`, `created_at`, `profile_image`, `tel`) VALUES
(34, 'ubann', 'titu', 'qwer@gmail.com', 'user', '7777777754545', '', 'scrypt:32768:8:1$NUevnNNTHXSBUFvB$74d34d9e28b8030da208d104ba294a9c8e4c538b0385f874dcb2408e5eb49ce944735c159b00df4bd2a902b0289bb571a2fbbc37c6b57f82bf6029a6435bd253', 'user', '2025-06-09 09:41:39', 'resume.jpg', '0987676789');

-- --------------------------------------------------------

--
-- Table structure for table `user_lesson_progress`
--

CREATE TABLE `user_lesson_progress` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `video_id` int(11) NOT NULL,
  `lesson_id` int(11) NOT NULL,
  `is_completed` tinyint(1) DEFAULT 0,
  `completed_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_lesson_progress`
--

INSERT INTO `user_lesson_progress` (`id`, `user_id`, `video_id`, `lesson_id`, `is_completed`, `completed_at`) VALUES
(8, 34, 63, 6, 1, '2025-07-21 01:38:16');

-- --------------------------------------------------------

--
-- Table structure for table `user_quiz_attempts`
--

CREATE TABLE `user_quiz_attempts` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `quiz_id` int(11) NOT NULL,
  `score` int(11) DEFAULT 0,
  `passed` tinyint(1) DEFAULT 0,
  `attempt_date` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_quiz_attempts`
--

INSERT INTO `user_quiz_attempts` (`id`, `user_id`, `quiz_id`, `score`, `passed`, `attempt_date`) VALUES
(21, 34, 42, 0, 1, '2025-07-21 01:46:25');

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
-- Indexes for table `instructor`
--
ALTER TABLE `instructor`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `lesson`
--
ALTER TABLE `lesson`
  ADD PRIMARY KEY (`lesson_id`);

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
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `id_card` (`id_card`);

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
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `instructor`
--
ALTER TABLE `instructor`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `lesson`
--
ALTER TABLE `lesson`
  MODIFY `lesson_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `questions`
--
ALTER TABLE `questions`
  MODIFY `question_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=40;

--
-- AUTO_INCREMENT for table `quiz`
--
ALTER TABLE `quiz`
  MODIFY `quiz_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=46;

--
-- AUTO_INCREMENT for table `quiz_video`
--
ALTER TABLE `quiz_video`
  MODIFY `video_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=68;

--
-- AUTO_INCREMENT for table `registered_courses`
--
ALTER TABLE `registered_courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT for table `user_lesson_progress`
--
ALTER TABLE `user_lesson_progress`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `user_quiz_attempts`
--
ALTER TABLE `user_quiz_attempts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`instructor_id`) REFERENCES `instructor` (`id`),
  ADD CONSTRAINT `courses_ibfk_2` FOREIGN KEY (`categories_id`) REFERENCES `categories` (`id`);

--
-- Constraints for table `questions`
--
ALTER TABLE `questions`
  ADD CONSTRAINT `fk_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`quiz_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `quiz`
--
ALTER TABLE `quiz`
  ADD CONSTRAINT `fk_quiz_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lesson` (`lesson_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `quiz_video`
--
ALTER TABLE `quiz_video`
  ADD CONSTRAINT `fk_quiz_video_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lesson` (`lesson_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_quiz_video_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`quiz_id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Constraints for table `registered_courses`
--
ALTER TABLE `registered_courses`
  ADD CONSTRAINT `registered_courses_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `registered_courses_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_lesson_progress`
--
ALTER TABLE `user_lesson_progress`
  ADD CONSTRAINT `user_lesson_progress_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `user_lesson_progress_ibfk_2` FOREIGN KEY (`video_id`) REFERENCES `quiz_video` (`video_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `user_lesson_progress_ibfk_3` FOREIGN KEY (`lesson_id`) REFERENCES `lesson` (`lesson_id`) ON DELETE CASCADE;

--
-- Constraints for table `user_quiz_attempts`
--
ALTER TABLE `user_quiz_attempts`
  ADD CONSTRAINT `user_quiz_attempts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `user_quiz_attempts_ibfk_2` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`quiz_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
