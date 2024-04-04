# Host: localhost  (Version: 5.7.26)
# Date: 2023-04-26 16:37:38
# Generator: MySQL-Front 5.3  (Build 4.234)

/*!40101 SET NAMES utf8 */;

#
# Structure for table "face"
#

DROP TABLE IF EXISTS `face`;
CREATE TABLE `face` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(10) DEFAULT NULL,
  `label` varchar(255) DEFAULT NULL,
  `face_data` mediumblob,
  PRIMARY KEY (`Id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
