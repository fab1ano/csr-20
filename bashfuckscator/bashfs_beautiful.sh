#!/bin/bash
echo "Welcome to bashfuckscator!";
echo "Press L for code listing, or enter code.";

read data;

if [ "${data}" = "L" ]; then
	cat $0;
	exit 0;
fi;

while [ ${i:-0} -lt ${#data} ]; do
	var="regs_${curreg:-0}";  # Set current variable
	var="${var/-/_}";
	curc="${data:$i:1}";  # Get current character

	[ "${curc}" = "$(((i+0)%10))" ]&&declare "${var}=$((${!var:-0}+1))";  # Increase value in current register
	[ "${curc}" = "$(((i+1)%10))" ]&&declare "${var}=$((${!var:-0}-1))";  # Decrease value in current register
	[ "${curc}" = "$(((i+2)%10))" ]&&printf -- "\x$(printf "%02x" "${!var}")";  # Output current register content as one byte
	[ "${curc}" = "$(((i+3)%10))" ]&&curreg=$((${curreg:-0}+1));  # Increase current register number
	[ "${curc}" = "$(((i+4)%10))" ]&&curreg=$((${curreg:-0}-1));  # Decrease current register number
	[ "${curc}" = "$(((i+5)%10))" ]&&echo "STDIN not implemented"&&exit 1;

	if [ "${curc}" = "$(((i+6)%10))" ]; then  # Go to loop end if current register is 0
		oldd=${loopd:-0};
		loopd=$((oldd+1));
		declare "loops_$loopd=$i";

		if [ ${!var:-0} -eq 0 ]; then
			while [ $oldd -lt $loopd ]; do
				i=$((${i:-0}+1));  # Increment counter

				if [ $i -eq ${#data} ]; then
					echo "LOOP ERROR";
					exit 1;
				fi;

				if [ "${data:$i:1}" = "$(((i+6)%10))" ]; then
					loopd=$((loopd+1));
				elif [ "${data:$i:1}" = "$(((i+7)%10))" ]; then
					loopd=$((loopd-1));
				fi;

			done;
		fi;

	elif [ "${curc}" = "$(((i+7)%10))" ]; then  # Go to loop start
		lvar="loops_${loopd:-0}";
		i=$((${!lvar}-1));
		loopd=$((${loopd:-0}-1));
	fi;


	# Increase counter
	i=$((${i:-0}+1));

done|sh

