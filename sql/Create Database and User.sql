
create database whiley;
create user 'whiley'@'%' identified by 'coyote';
grant all on whiley to whiley identified by 'coyote';
grant all on whiley.* to whiley identified by 'coyote';

