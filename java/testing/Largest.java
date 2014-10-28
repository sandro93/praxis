public class Largest{
	/** Return the largest element int at list
	 *
	 * @param list A list of integers
	 * @return the largest number in the given list. 
	 */
	public static int largest(int[] list){
		int i, max = Integer.MIN_VALUE;
		if(list.length == 0){
			throw new RuntimeException("Empty list");
		}
		for(i = 0; i < list.length; i++){
			if(list[i] > max){
				max = list[i];
			}
		}
		return max;
	}
}
