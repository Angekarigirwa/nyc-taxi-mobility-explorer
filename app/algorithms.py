from __future__ import annotations

from typing import List, Tuple, Any, Hashable


class MinHeap:
	"""Custom min-heap implementation without using heapq library"""
	
	def __init__(self):
		self.heap = []
	
	def _parent(self, i: int) -> int:
		return (i - 1) // 2
	
	def _left(self, i: int) -> int:
		return 2 * i + 1
	
	def _right(self, i: int) -> int:
		return 2 * i + 2
	
	def _swap(self, i: int, j: int) -> None:
		self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
	
	def _heapify_up(self, i: int) -> None:
		while i > 0:
			parent = self._parent(i)
			if self.heap[parent][0] <= self.heap[i][0]:
				break
			self._swap(i, parent)
			i = parent
	
	def _heapify_down(self, i: int) -> None:
		while True:
			left = self._left(i)
			right = self._right(i)
			smallest = i
			
			if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]:
				smallest = left
			if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]:
				smallest = right
			
			if smallest == i:
				break
			
			self._swap(i, smallest)
			i = smallest
	
	def push(self, item: Tuple[float, Any]) -> None:
		"""Add item to heap. Item should be (priority, value) tuple"""
		self.heap.append(item)
		self._heapify_up(len(self.heap) - 1)
	
	def pop(self) -> Tuple[float, Any] | None:
		"""Remove and return minimum item"""
		if not self.heap:
			return None
		
		if len(self.heap) == 1:
			return self.heap.pop()
		
		min_item = self.heap[0]
		self.heap[0] = self.heap.pop()
		self._heapify_down(0)
		return min_item
	
	def peek(self) -> Tuple[float, Any] | None:
		"""Return minimum item without removing"""
		return self.heap[0] if self.heap else None
	
	def __len__(self) -> int:
		return len(self.heap)


class TopKFrequent:
	"""Custom Top-K frequent elements algorithm using min-heap"""
	
	def __init__(self, k: int):
		self.k = k
		self.heap = MinHeap()
		self.counts = {}
	
	def add(self, item: Hashable, count: int = 1) -> None:
		"""Add item with count to the data structure"""
		if item in self.counts:
			self.counts[item] += count
		else:
			self.counts[item] = count
		
		# Update heap
		if len(self.heap) < self.k:
			self.heap.push((self.counts[item], item))
		else:
			min_item = self.heap.peek()
			if min_item and self.counts[item] > min_item[0]:
				self.heap.pop()
				self.heap.push((self.counts[item], item))
	
	def get_top_k(self) -> List[Tuple[Any, int]]:
		"""Get top K most frequent items as (item, count) tuples"""
		result = []
		temp_heap = MinHeap()
		
		# Extract all items from heap
		while self.heap:
			item = self.heap.pop()
			if item:
				temp_heap.push(item)
		
		# Sort by count descending
		items = []
		while temp_heap:
			item = temp_heap.pop()
			if item:
				items.append(item)
		
		# Sort by count descending
		items.sort(key=lambda x: x[0], reverse=True)
		
		return [(item, count) for count, item in items]


class MedianCalculator:
	"""Custom median calculator using two heaps"""
	
	def __init__(self):
		self.max_heap = []  # Left side (smaller numbers)
		self.min_heap = []  # Right side (larger numbers)
	
	def _parent(self, i: int) -> int:
		return (i - 1) // 2
	
	def _left(self, i: int) -> int:
		return 2 * i + 1
	
	def _right(self, i: int) -> int:
		return 2 * i + 2
	
	def _max_heapify_up(self, i: int) -> None:
		"""Heapify up for max heap"""
		while i > 0:
			parent = self._parent(i)
			if self.max_heap[parent] >= self.max_heap[i]:
				break
			self.max_heap[i], self.max_heap[parent] = self.max_heap[parent], self.max_heap[i]
			i = parent
	
	def _min_heapify_up(self, i: int) -> None:
		"""Heapify up for min heap"""
		while i > 0:
			parent = self._parent(i)
			if self.min_heap[parent] <= self.min_heap[i]:
				break
			self.min_heap[i], self.min_heap[parent] = self.min_heap[parent], self.min_heap[i]
			i = parent
	
	def _max_heapify_down(self, i: int) -> None:
		"""Heapify down for max heap"""
		while True:
			left = self._left(i)
			right = self._right(i)
			largest = i
			
			if left < len(self.max_heap) and self.max_heap[left] > self.max_heap[largest]:
				largest = left
			if right < len(self.max_heap) and self.max_heap[right] > self.max_heap[largest]:
				largest = right
			
			if largest == i:
				break
			
			self.max_heap[i], self.max_heap[largest] = self.max_heap[largest], self.max_heap[i]
			i = largest
	
	def _min_heapify_down(self, i: int) -> None:
		"""Heapify down for min heap"""
		while True:
			left = self._left(i)
			right = self._right(i)
			smallest = i
			
			if left < len(self.min_heap) and self.min_heap[left] < self.min_heap[smallest]:
				smallest = left
			if right < len(self.min_heap) and self.min_heap[right] < self.min_heap[smallest]:
				smallest = right
			
			if smallest == i:
				break
			
			self.min_heap[i], self.min_heap[smallest] = self.min_heap[smallest], self.min_heap[i]
			i = smallest
	
	def _extract_max(self) -> float:
		"""Extract max from max heap"""
		if not self.max_heap:
			raise ValueError("Max heap is empty")
		
		if len(self.max_heap) == 1:
			return self.max_heap.pop()
		
		max_val = self.max_heap[0]
		self.max_heap[0] = self.max_heap.pop()
		self._max_heapify_down(0)
		return max_val
	
	def _extract_min(self) -> float:
		"""Extract min from min heap"""
		if not self.min_heap:
			raise ValueError("Min heap is empty")
		
		if len(self.min_heap) == 1:
			return self.min_heap.pop()
		
		min_val = self.min_heap[0]
		self.min_heap[0] = self.min_heap.pop()
		self._min_heapify_down(0)
		return min_val
	
	def add(self, value: float) -> None:
		"""Add value to the median calculator"""
		if not self.max_heap or value <= self.max_heap[0]:
			# Add to max heap
			self.max_heap.append(value)
			self._max_heapify_up(len(self.max_heap) - 1)
		else:
			# Add to min heap
			self.min_heap.append(value)
			self._min_heapify_up(len(self.min_heap) - 1)
		
		# Balance heaps
		if len(self.max_heap) > len(self.min_heap) + 1:
			# Move from max heap to min heap
			val = self._extract_max()
			self.min_heap.append(val)
			self._min_heapify_up(len(self.min_heap) - 1)
		elif len(self.min_heap) > len(self.max_heap) + 1:
			# Move from min heap to max heap
			val = self._extract_min()
			self.max_heap.append(val)
			self._max_heapify_up(len(self.max_heap) - 1)
	
	def get_median(self) -> float:
		"""Get current median"""
		if not self.max_heap and not self.min_heap:
			raise ValueError("No values added")
		
		if len(self.max_heap) == len(self.min_heap):
			return (self.max_heap[0] + self.min_heap[0]) / 2
		elif len(self.max_heap) > len(self.min_heap):
			return self.max_heap[0]
		else:
			return self.min_heap[0]


class AnomalyDetector:
	"""Custom anomaly detection using rolling statistics"""
	
	def __init__(self, window_size: int = 100, threshold: float = 2.5):
		self.window_size = window_size
		self.threshold = threshold
		self.values = []
		self.mean = 0.0
		self.variance = 0.0
	
	def add(self, value: float) -> bool:
		"""Add value and return True if it's an anomaly"""
		self.values.append(value)
		
		# Keep only recent values
		if len(self.values) > self.window_size:
			self.values.pop(0)
		
		# Update statistics
		n = len(self.values)
		if n == 1:
			self.mean = value
			self.variance = 0.0
			return False
		
		# Online mean update
		old_mean = self.mean
		self.mean = old_mean + (value - old_mean) / n
		
		# Online variance update (Welford's algorithm)
		if n > 1:
			self.variance = ((n - 2) * self.variance + (value - old_mean) * (value - self.mean)) / (n - 1)
		
		# Check for anomaly
		if n < 3:  # Need at least 3 values for meaningful z-score
			return False
		
		std_dev = (self.variance ** 0.5) if self.variance > 0 else 0
		if std_dev == 0:
			return False
		
		z_score = abs(value - self.mean) / std_dev
		return z_score > self.threshold
