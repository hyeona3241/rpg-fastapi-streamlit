-- mysql -u root -pbitnami mysql < create_db.sql

use mysql;
drop user if exists 'rpg'@'localhost';
create user 'rpg'@'localhost' identified by 'rpg';
flush privileges; 
drop database if exists MyRPG;
select '' as 'show databases';
show databases;

create database MyRPG;
grant all on MyRPG.* to 'rpg'@'localhost';
flush privileges;
commit;
select '' as 'show newly created databases';
show databases;

