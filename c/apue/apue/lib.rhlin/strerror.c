#include	<stdio.h>

/* thextern char	*sys_errlist[]; */
extern int	sys_nerr;

char *
strerror(int error)
{
	static char	mesg[30];

	if (error >= 0 && error <= sys_nerr)
		return(sys_errlist[error]);

	sprintf(mesg, "Unknown error (%d)", error);
	return(mesg);
}
