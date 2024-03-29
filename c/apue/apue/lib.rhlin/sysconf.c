#include	<sys/types.h>
#include	<sys/param.h>
#include	<errno.h>
#include	<limits.h>
#include	<unistd.h>
#include	<timebits.h>

long
sysconf(int name)
{
	switch (name) {
	case _SC_ARG_MAX:	return(ARG_MAX);
	case _SC_CHILD_MAX:	return(CHILD_MAX);
	case _SC_CLK_TCK:	return(CLK_TCK);
	case _SC_NGROUPS_MAX:	return(NGROUPS_MAX);
	case _SC_OPEN_MAX:	return(OPEN_MAX);
		/* Could actually call getdtablesize() or getrlimit(),
		   since OPEN_MAX isn't really the limit */
	case _SC_VERSION:	return(_POSIX_VERSION);

	case _SC_JOB_CONTROL:
#ifdef	_POSIX_JOB_CONTROL	/* always true for BSD */
		return(1);
#else
		return(-1);
#endif

	case _SC_SAVED_IDS:
#ifdef	_POSIX_SAVED_IDS	/* not true yet for BSD */
		return(1);
#else
		return(-1);
#endif

	default:	
		errno = EINVAL;
		return(-1);
	}
}
